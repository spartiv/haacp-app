import SwiftUI

struct DashboardView: View {
    @Environment(AuthStore.self) private var authStore
    @State private var dashboard: DashboardResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var controlPeriod: ControlPeriod?
    @State private var showProducts = false
    @State private var showAddProduct = false
    @State private var newProductName = ""
    @State private var createdProduct: ProductResponse?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && dashboard == nil {
                ProgressView()
                    .tint(.hAccent)
            } else {
                ScrollView {
                    VStack(spacing: 20) {
                        overviewGrid
                        if let items = dashboard?.attentionItems, !items.isEmpty {
                            attentionSection(items: items)
                        }
                    }
                    .padding()
                }
                .refreshable { await load() }
            }
        }
        .navigationTitle("Огляд")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showAddProduct = true } label: {
                    Image(systemName: "plus").foregroundStyle(Color.hAccent)
                }
            }
        }
        .navigationDestination(item: $controlPeriod) { period in
            ControlRecordView(period: period)
        }
        .navigationDestination(isPresented: $showProducts) {
            HomeView()
        }
        .navigationDestination(item: $createdProduct) { product in
            ProductDetailView(product: product)
        }
        .task { await load() }
        .alert("Новий продукт", isPresented: $showAddProduct) {
            TextField("Назва продукту", text: $newProductName)
            Button("Скасувати", role: .cancel) { newProductName = "" }
            Button("Додати") { Task { await addProduct() } }
        }
        .alert("Помилка", isPresented: Binding(get: { errorMessage != nil }, set: { if !$0 { errorMessage = nil } }), actions: {
            Button("OK") { errorMessage = nil }
        }, message: {
            Text(errorMessage ?? "")
        })
    }

    // MARK: - Sections

    private var overviewGrid: some View {
        LazyVGrid(
            columns: Array(repeating: GridItem(.flexible(), spacing: 12), count: 3),
            spacing: 12
        ) {
            ControlCard(title: "Щоденний", status: dashboard?.dailyControl) {
                controlPeriod = .daily
            }
            ControlCard(title: "Місячний", status: dashboard?.monthlyControl) {
                controlPeriod = .monthly
            }
            BatchCard(count: dashboard?.batchesThisMonth) {
                showProducts = true
            }
        }
    }

    private func attentionSection(items: [AttentionItemResponse]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Увага")
                .font(.headline)
                .foregroundStyle(Color.hTextPrimary)

            VStack(spacing: 8) {
                ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                    AttentionRow(item: item)
                }
            }
        }
    }

    // MARK: - Load

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            dashboard = try await authStore.call { token in
                guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                return try await APIClient.getDashboard(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func addProduct() async {
        guard let orgId = authStore.organizationId else {
            errorMessage = HaacpError.unauthorized.errorDescription
            return
        }
        let name = newProductName.trimmingCharacters(in: .whitespaces)
        newProductName = ""
        guard !name.isEmpty else { return }
        do {
            let product = try await authStore.call { token in
                try await APIClient.createProduct(orgId: orgId, name: name, token: token)
            }
            createdProduct = product
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}

// MARK: - Sub-views

private struct ControlCard: View {
    let title: String
    let status: ControlStatusResponse?
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
                    .lineLimit(1)

                if let status {
                    Circle()
                        .fill(statusColor(status))
                        .frame(width: 10, height: 10)
                    Text(statusLabel(status))
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(Color.hTextPrimary)
                        .lineLimit(2)
                        .fixedSize(horizontal: false, vertical: true)
                } else {
                    ProgressView().scaleEffect(0.6)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .padding(12)
            .background(Color.hSurface)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
        .buttonStyle(.plain)
    }

    private func statusColor(_ s: ControlStatusResponse) -> Color {
        if !s.filled { return .yellow }
        if s.hasDeviation == true { return .orange }
        return .green
    }

    private func statusLabel(_ s: ControlStatusResponse) -> String {
        if !s.filled { return "Не заповнено" }
        if s.hasDeviation == true { return "Відхилення" }
        return "Заповнено"
    }
}

private struct BatchCard: View {
    let count: Int?
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                Text("Партії")
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
                    .lineLimit(1)

                if let count {
                    Image(systemName: "shippingbox.fill")
                        .font(.caption)
                        .foregroundStyle(Color.hAccent.opacity(0.7))
                    Text("\(count) / міс.")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(Color.hTextPrimary)
                        .lineLimit(1)
                } else {
                    ProgressView().scaleEffect(0.6)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .padding(12)
            .background(Color.hSurface)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
        .buttonStyle(.plain)
    }
}

private struct AttentionRow: View {
    let item: AttentionItemResponse

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: iconName)
                .foregroundStyle(iconColor)
                .frame(width: 20)
            VStack(alignment: .leading, spacing: 2) {
                Text(item.label)
                    .font(.subheadline)
                    .foregroundStyle(Color.hTextPrimary)
                Text(daysLabel)
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
            }
            Spacer()
        }
        .padding()
        .background(Color.hSurface)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var iconName: String {
        switch item.severity {
        case "critical": return "exclamationmark.circle.fill"
        case "warning": return "exclamationmark.triangle.fill"
        default: return "info.circle.fill"
        }
    }

    private var iconColor: Color {
        switch item.severity {
        case "critical": return .hDeviationRed
        case "warning": return .orange
        default: return .hAccent
        }
    }

    private var daysLabel: String {
        if item.days < 0 { return "Прострочено на \(-item.days) дн." }
        if item.days == 0 { return "Сьогодні" }
        return "Через \(item.days) дн."
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        DashboardView()
            .environment(store)
    }
}
