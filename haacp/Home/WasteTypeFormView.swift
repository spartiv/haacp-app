import SwiftUI

struct WasteTypeFormView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    let existing: WasteTypeResponse?
    let onSaved: (WasteTypeResponse) -> Void

    @State private var name: String
    @State private var disposalMethod: String

    @State private var isSaving = false
    @State private var errorMessage: String?

    init(onSaved: @escaping (WasteTypeResponse) -> Void) {
        self.existing = nil
        self.onSaved = onSaved
        _name = State(initialValue: "")
        _disposalMethod = State(initialValue: "")
    }

    init(existing: WasteTypeResponse, onSaved: @escaping (WasteTypeResponse) -> Void) {
        self.existing = existing
        self.onSaved = onSaved
        _name = State(initialValue: existing.name)
        _disposalMethod = State(initialValue: existing.disposalMethod)
    }

    private var isValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty &&
        !disposalMethod.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.hBackground.ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Назва")
                                .font(.headline).foregroundStyle(Color.hTextPrimary)
                            HaacpTextField("Назва типу відходів *", text: $name)
                        }

                        VStack(alignment: .leading, spacing: 8) {
                            Text("Спосіб утилізації")
                                .font(.headline).foregroundStyle(Color.hTextPrimary)
                            TextEditor(text: $disposalMethod)
                                .frame(minHeight: 100)
                                .padding(10)
                                .background(Color.hSurface)
                                .clipShape(RoundedRectangle(cornerRadius: 10))
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
                        }

                        if let error = errorMessage {
                            Text(error).font(.caption).foregroundStyle(Color.hDeviationRed)
                        }

                        HaacpButton(existing == nil ? "Додати тип" : "Зберегти зміни", isLoading: isSaving) {
                            await save()
                        }
                        .opacity(isValid ? 1 : 0.5)
                        .disabled(!isValid)
                    }
                    .padding()
                }
            }
            .navigationTitle(existing == nil ? "Новий тип відходів" : "Редагувати")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Скасувати") { dismiss() }
                        .foregroundStyle(Color.hTextSecondary)
                }
            }
        }
    }

    private func save() async {
        guard let orgId = authStore.organizationId else { return }
        isSaving = true
        defer { isSaving = false }
        do {
            let saved: WasteTypeResponse
            if let existing {
                saved = try await authStore.call { token in
                    try await APIClient.updateWasteType(orgId: orgId, wasteTypeId: existing.id, body: WasteTypeUpdateRequest(
                        name: name.trimmingCharacters(in: .whitespaces),
                        disposalMethod: disposalMethod.trimmingCharacters(in: .whitespaces)
                    ), token: token)
                }
            } else {
                saved = try await authStore.call { token in
                    try await APIClient.createWasteType(orgId: orgId, body: WasteTypeCreateRequest(
                        name: name.trimmingCharacters(in: .whitespaces),
                        disposalMethod: disposalMethod.trimmingCharacters(in: .whitespaces)
                    ), token: token)
                }
            }
            onSaved(saved)
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}
