import SwiftUI

struct EquipmentListView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var equipment: [EquipmentResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showAddForm = false
    @State private var editingItem: EquipmentResponse?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && equipment.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else if equipment.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "gearshape.2")
                        .font(.system(size: 48))
                        .foregroundStyle(Color.hAccent.opacity(0.5))
                    Text("Обладнання відсутнє")
                        .foregroundStyle(Color.hTextSecondary)
                    Button { showAddForm = true } label: {
                        Text("Додати перше обладнання").foregroundStyle(Color.hAccent)
                    }
                }
            } else {
                List {
                    ForEach(equipment) { item in
                        Button { editingItem = item } label: {
                            EquipmentRow(item: item)
                        }
                        .buttonStyle(.plain)
                        .listRowBackground(Color.hSurface)
                    }
                    .onDelete { indexSet in
                        Task { await deleteEquipment(at: indexSet) }
                    }
                }
                .scrollContentBackground(.hidden)
                .refreshable { await load() }
            }
        }
        .navigationTitle("Обладнання")
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
            EquipmentFormView { newItem in
                equipment.append(newItem)
                showAddForm = false
            }
        }
        .sheet(item: $editingItem) { item in
            EquipmentFormView(existing: item) { updated in
                if let idx = equipment.firstIndex(where: { $0.id == updated.id }) {
                    equipment[idx] = updated
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
            equipment = try await authStore.call { token in
                try await APIClient.listEquipment(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func deleteEquipment(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let item = equipment[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteEquipment(orgId: orgId, equipmentId: item.id, token: token)
                }
                equipment.remove(at: index)
            } catch {
                errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
            }
        }
    }
}

private struct EquipmentRow: View {
    let item: EquipmentResponse

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(item.name)
                        .font(.headline)
                        .foregroundStyle(Color.hTextPrimary)
                    if item.affectsProductSafety {
                        Image(systemName: "exclamationmark.shield.fill")
                            .font(.caption)
                            .foregroundStyle(Color.hDeviationRed)
                    }
                }
                Text("\(item.type.displayName) · \(item.amount) од. · \(item.frequency)")
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
