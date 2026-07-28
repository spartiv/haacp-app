import SwiftUI

struct ChemicalListView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var chemicals: [ChemicalResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showAddForm = false
    @State private var editingItem: ChemicalResponse?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && chemicals.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else if chemicals.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "flask")
                        .font(.system(size: 48))
                        .foregroundStyle(Color.hAccent.opacity(0.5))
                    Text("Хімічних засобів немає")
                        .foregroundStyle(Color.hTextSecondary)
                    Button { showAddForm = true } label: {
                        Text("Додати перший засіб").foregroundStyle(Color.hAccent)
                    }
                }
            } else {
                List {
                    ForEach(chemicals) { item in
                        Button { editingItem = item } label: {
                            ChemicalRow(item: item)
                        }
                        .buttonStyle(.plain)
                        .listRowBackground(Color.hSurface)
                    }
                    .onDelete { indexSet in
                        Task { await deleteChemicals(at: indexSet) }
                    }
                }
                .scrollContentBackground(.hidden)
                .refreshable { await load() }
            }
        }
        .navigationTitle("Хімічні засоби")
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
            ChemicalFormView { newItem in
                chemicals.append(newItem)
                showAddForm = false
            }
        }
        .sheet(item: $editingItem) { item in
            ChemicalFormView(existing: item) { updated in
                if let idx = chemicals.firstIndex(where: { $0.id == updated.id }) {
                    chemicals[idx] = updated
                }
                editingItem = nil
            }
        }
        .alert("Помилка", isPresented: .constant(errorMessage != nil)) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task { await load() }
    }

    private func load() async {
        guard let orgId = authStore.organizationId else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            chemicals = try await authStore.call { token in
                try await APIClient.listChemicals(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func deleteChemicals(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let item = chemicals[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteChemical(orgId: orgId, chemicalId: item.id, token: token)
                }
                chemicals.remove(at: index)
            } catch {
                errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
            }
        }
    }
}

private struct ChemicalRow: View {
    let item: ChemicalResponse

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name)
                    .font(.headline)
                    .foregroundStyle(Color.hTextPrimary)
                Text(item.category.displayName)
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color.hTextSecondary)
        }
        .padding(.vertical, 4)
    }
}
