import SwiftUI

struct AllergenListView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var allergens: [AllergenStatusResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && allergens.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else {
                List(allergens.sorted { $0.position < $1.position }) { allergen in
                    AllergenRow(allergen: allergen) { newPresent in
                        await togglePresence(allergen: allergen, present: newPresent)
                    }
                    .listRowBackground(Color.hSurface)
                }
                .scrollContentBackground(.hidden)
                .refreshable { await load() }
            }
        }
        .navigationTitle("Алергени")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
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
            allergens = try await authStore.call { token in
                try await APIClient.listAllergens(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func togglePresence(allergen: AllergenStatusResponse, present: Bool) async {
        guard let orgId = authStore.organizationId else { return }
        // Optimistic update
        if let idx = allergens.firstIndex(where: { $0.allergenId == allergen.allergenId }) {
            allergens[idx] = AllergenStatusResponse(
                allergenId: allergen.allergenId,
                name: allergen.name,
                position: allergen.position,
                present: present
            )
        }
        do {
            let updated = try await authStore.call { token in
                try await APIClient.updateAllergenPresence(orgId: orgId, allergenId: allergen.allergenId, present: present, token: token)
            }
            if let idx = allergens.firstIndex(where: { $0.allergenId == updated.allergenId }) {
                allergens[idx] = updated
            }
        } catch {
            // Revert on failure
            if let idx = allergens.firstIndex(where: { $0.allergenId == allergen.allergenId }) {
                allergens[idx] = allergen
            }
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}

private struct AllergenRow: View {
    let allergen: AllergenStatusResponse
    let onToggle: (Bool) async -> Void

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(allergen.name)
                    .font(.headline)
                    .foregroundStyle(Color.hTextPrimary)
                Text(allergen.present ? "Присутній" : "Відсутній")
                    .font(.caption)
                    .foregroundStyle(allergen.present ? Color.hDeviationRed : Color.hTextSecondary)
            }
            Spacer()
            Toggle("", isOn: Binding(
                get: { allergen.present },
                set: { newValue in Task { await onToggle(newValue) } }
            ))
            .labelsHidden()
            .tint(Color.hDeviationRed)
        }
        .padding(.vertical, 4)
    }
}
