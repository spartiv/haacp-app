import SwiftUI

struct WasteTypeListView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var wasteTypes: [WasteTypeResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showAddForm = false
    @State private var editingItem: WasteTypeResponse?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && wasteTypes.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else if wasteTypes.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "trash")
                        .font(.system(size: 48))
                        .foregroundStyle(Color.hAccent.opacity(0.5))
                    Text("Типів відходів немає")
                        .foregroundStyle(Color.hTextSecondary)
                    Button { showAddForm = true } label: {
                        Text("Додати перший тип").foregroundStyle(Color.hAccent)
                    }
                }
            } else {
                List {
                    ForEach(wasteTypes) { item in
                        Button { editingItem = item } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.name)
                                    .font(.headline)
                                    .foregroundStyle(Color.hTextPrimary)
                                Text(item.disposalMethod)
                                    .font(.caption)
                                    .foregroundStyle(Color.hTextSecondary)
                                    .lineLimit(2)
                            }
                            .padding(.vertical, 4)
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
        .navigationTitle("Типи відходів")
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
            WasteTypeFormView { newItem in
                wasteTypes.append(newItem)
                showAddForm = false
            }
        }
        .sheet(item: $editingItem) { item in
            WasteTypeFormView(existing: item) { updated in
                if let idx = wasteTypes.firstIndex(where: { $0.id == updated.id }) {
                    wasteTypes[idx] = updated
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
            wasteTypes = try await authStore.call { token in
                try await APIClient.listWasteTypes(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func deleteItems(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let item = wasteTypes[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteWasteType(orgId: orgId, wasteTypeId: item.id, token: token)
                }
                wasteTypes.remove(at: index)
            } catch {
                errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
            }
        }
    }
}
