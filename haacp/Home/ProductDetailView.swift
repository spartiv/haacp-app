import SwiftUI

struct ProductDetailView: View {
    @Environment(AuthStore.self) private var authStore
    let product: ProductResponse

    @State private var selectedTab = 0

    @State private var batches: [BatchResponse] = []
    @State private var isLoadingBatches = false

    @State private var checklistItems: [ChecklistItemResponse] = []
    @State private var isLoadingChecklist = false

    @State private var showRecordBatch = false
    @State private var selectedBatch: BatchResponse?

    @State private var showAddChecklist = false
    @State private var newItemLabel = ""

    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 0) {
            Picker("", selection: $selectedTab) {
                Text("Партії").tag(0)
                Text("Чеклист").tag(1)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .padding(.vertical, 10)
            .background(Color.hBackground)

            if selectedTab == 0 {
                batchesSection
            } else {
                checklistSection
            }
        }
        .background(Color.hBackground.ignoresSafeArea())
        .navigationTitle(product.name)
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    if selectedTab == 0 { showRecordBatch = true }
                    else { showAddChecklist = true }
                } label: {
                    Image(systemName: "plus").foregroundStyle(Color.hAccent)
                }
            }
        }
        .navigationDestination(isPresented: $showRecordBatch) {
            BatchRecordView(product: product) { batch in
                batches.insert(batch, at: 0)
                showRecordBatch = false
            }
        }
        .navigationDestination(item: $selectedBatch) { batch in
            BatchDetailView(
                batch: batch,
                product: product,
                onUpdated: { updated in
                    if let idx = batches.firstIndex(where: { $0.id == updated.id }) {
                        batches[idx] = updated
                    }
                },
                onDeleted: {
                    batches.removeAll { $0.id == batch.id }
                }
            )
        }
        .alert("Нове питання", isPresented: $showAddChecklist) {
            TextField("Текст питання", text: $newItemLabel)
            Button("Скасувати", role: .cancel) { newItemLabel = "" }
            Button("Додати") { Task { await addChecklistItem() } }
        }
        .alert("Помилка", isPresented: .constant(errorMessage != nil)) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task {
            await loadBatches()
            await loadChecklist()
        }
    }

    // MARK: - Batches tab

    @ViewBuilder
    private var batchesSection: some View {
        if isLoadingBatches && batches.isEmpty {
            Spacer()
            ProgressView().tint(Color.hAccent)
            Spacer()
        } else if batches.isEmpty {
            Spacer()
            VStack(spacing: 16) {
                Image(systemName: "list.clipboard")
                    .font(.system(size: 48))
                    .foregroundStyle(Color.hAccent.opacity(0.5))
                Text("Партії відсутні")
                    .foregroundStyle(Color.hTextSecondary)
                Button { showRecordBatch = true } label: {
                    Text("Записати першу партію").foregroundStyle(Color.hAccent)
                }
            }
            Spacer()
        } else {
            List {
                ForEach(batches) { batch in
                    Button { selectedBatch = batch } label: {
                        BatchRow(batch: batch)
                    }
                    .buttonStyle(.plain)
                    .listRowBackground(Color.hSurface)
                }
                .onDelete { indexSet in
                    Task { await deleteBatches(at: indexSet) }
                }
            }
            .scrollContentBackground(.hidden)
            .refreshable { await loadBatches() }
        }
    }

    // MARK: - Checklist tab

    @ViewBuilder
    private var checklistSection: some View {
        if isLoadingChecklist && checklistItems.isEmpty {
            Spacer()
            ProgressView().tint(Color.hAccent)
            Spacer()
        } else if checklistItems.isEmpty {
            Spacer()
            VStack(spacing: 12) {
                Image(systemName: "checklist")
                    .font(.system(size: 48))
                    .foregroundStyle(Color.hAccent.opacity(0.5))
                Text("Чеклист порожній")
                    .foregroundStyle(Color.hTextSecondary)
                Button { showAddChecklist = true } label: {
                    Text("Додати перше питання").foregroundStyle(Color.hAccent)
                }
            }
            Spacer()
        } else {
            List {
                ForEach(checklistItems.sorted { $0.position < $1.position }) { item in
                    HStack {
                        Text("\(item.position).")
                            .font(.caption)
                            .foregroundStyle(Color.hTextSecondary)
                            .frame(width: 24, alignment: .leading)
                        Text(item.label)
                            .font(.body)
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .padding(.vertical, 4)
                    .listRowBackground(Color.hSurface)
                }
                .onDelete { indexSet in
                    Task { await deleteChecklistItems(at: indexSet) }
                }
            }
            .scrollContentBackground(.hidden)
            .refreshable { await loadChecklist() }
        }
    }

    // MARK: - Network

    private func loadBatches() async {
        guard let orgId = authStore.organizationId else { return }
        isLoadingBatches = true
        defer { isLoadingBatches = false }
        do {
            batches = try await authStore.call { token in
                try await APIClient.listBatches(orgId: orgId, productId: product.id, token: token)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func loadChecklist() async {
        guard let orgId = authStore.organizationId else { return }
        isLoadingChecklist = true
        defer { isLoadingChecklist = false }
        do {
            checklistItems = try await authStore.call { token in
                try await APIClient.listChecklistItems(orgId: orgId, productId: product.id, token: token)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func addChecklistItem() async {
        guard let orgId = authStore.organizationId else { return }
        let label = newItemLabel.trimmingCharacters(in: .whitespaces)
        newItemLabel = ""
        guard !label.isEmpty else { return }
        do {
            let item = try await authStore.call { token in
                try await APIClient.addChecklistItem(orgId: orgId, productId: product.id, label: label, token: token)
            }
            checklistItems.append(item)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func deleteChecklistItems(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        let sorted = checklistItems.sorted { $0.position < $1.position }
        for index in indexSet {
            let item = sorted[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteChecklistItem(orgId: orgId, productId: product.id, itemId: item.id, token: token)
                }
                checklistItems.removeAll { $0.id == item.id }
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func deleteBatches(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let batch = batches[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteBatch(orgId: orgId, batchId: batch.id, token: token)
                }
                batches.remove(at: index)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}

// MARK: - Batch row

struct BatchRow: View {
    let batch: BatchResponse

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("Партія №\(batch.number)")
                        .font(.headline)
                        .foregroundStyle(Color.hTextPrimary)
                    if batch.hasDeviation {
                        Label("Відхилення", systemImage: "exclamationmark.triangle.fill")
                            .font(.caption)
                            .foregroundStyle(Color.hDeviationRed)
                    }
                }
                HStack(spacing: 4) {
                    Text(batch.productionDate)
                        .font(.caption)
                        .foregroundStyle(Color.hTextSecondary)
                    if let name = batch.name {
                        Text("· \(name)")
                            .font(.caption)
                            .foregroundStyle(Color.hTextSecondary)
                    }
                }
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color.hTextSecondary)
        }
        .padding(.vertical, 4)
    }
}
