import SwiftUI

struct MedicalCheckListView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var checks: [MedicalCheckResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showAddForm = false
    @State private var editingItem: MedicalCheckResponse?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && checks.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else if checks.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "heart.text.clipboard")
                        .font(.system(size: 48))
                        .foregroundStyle(Color.hAccent.opacity(0.5))
                    Text("Записів медоглядів немає")
                        .foregroundStyle(Color.hTextSecondary)
                    Button { showAddForm = true } label: {
                        Text("Додати перший запис").foregroundStyle(Color.hAccent)
                    }
                }
            } else {
                List {
                    ForEach(checks) { item in
                        Button { editingItem = item } label: {
                            MedicalCheckRow(item: item)
                        }
                        .buttonStyle(.plain)
                        .listRowBackground(Color.hSurface)
                    }
                    .onDelete { indexSet in
                        Task { await deleteItems(at: indexSet) }
                    }
                }
                .scrollContentBackground(.hidden)
                .refreshable { await load() }
            }
        }
        .navigationTitle("Медогляди")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showAddForm = true } label: {
                    Image(systemName: "plus").foregroundStyle(Color.hAccent)
                }
            }
        }
        .sheet(isPresented: $showAddForm) {
            MedicalCheckFormView { newItem in
                checks.append(newItem)
                showAddForm = false
            }
        }
        .sheet(item: $editingItem) { item in
            MedicalCheckFormView(existing: item) { updated in
                if let idx = checks.firstIndex(where: { $0.id == updated.id }) {
                    checks[idx] = updated
                }
                editingItem = nil
            }
        }
        .alert("Помилка", isPresented: .constant(errorMessage != nil)) {
            Button("OK") { errorMessage = nil }
        } message: { Text(errorMessage ?? "") }
        .task { await load() }
    }

    private func load() async {
        guard let orgId = authStore.organizationId else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            checks = try await authStore.call { token in
                try await APIClient.listMedicalChecks(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func deleteItems(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let item = checks[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteMedicalCheck(orgId: orgId, checkId: item.id, token: token)
                }
                checks.remove(at: index)
            } catch {
                errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
            }
        }
    }
}

private struct MedicalCheckRow: View {
    let item: MedicalCheckResponse

    private var urgency: (label: String, color: Color) {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        guard let date = formatter.date(from: item.nextCheckDate) else {
            return ("Дата невідома", Color.hTextSecondary)
        }
        let days = Calendar.current.dateComponents([.day], from: Date(), to: date).day ?? 0
        if days < 0    { return ("Прострочено на \(-days) дн.", Color.hDeviationRed) }
        if days <= 14  { return ("Через \(days) дн.", .orange) }
        return ("Через \(days) дн.", Color.hTextSecondary)
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(item.employeeName)
                    .font(.headline).foregroundStyle(Color.hTextPrimary)
                HStack(spacing: 4) {
                    Text("Наступний огляд:")
                        .font(.caption).foregroundStyle(Color.hTextSecondary)
                    Text(item.nextCheckDate)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(urgency.color)
                    Text("·")
                        .font(.caption).foregroundStyle(Color.hTextSecondary)
                    Text(urgency.label)
                        .font(.caption).foregroundStyle(urgency.color)
                }
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.caption).foregroundStyle(Color.hTextSecondary)
        }
        .padding(.vertical, 4)
    }
}
