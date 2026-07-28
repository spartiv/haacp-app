import SwiftUI

struct EquipmentFormView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    let existing: EquipmentResponse?
    let onSaved: (EquipmentResponse) -> Void

    @State private var name: String
    @State private var type: EquipmentType
    @State private var frequency: String
    @State private var amount: Int
    @State private var affectsProductSafety: Bool

    @State private var isSaving = false
    @State private var errorMessage: String?

    init(onSaved: @escaping (EquipmentResponse) -> Void) {
        self.existing = nil
        self.onSaved = onSaved
        _name = State(initialValue: "")
        _type = State(initialValue: .production)
        _frequency = State(initialValue: "")
        _amount = State(initialValue: 1)
        _affectsProductSafety = State(initialValue: false)
    }

    init(existing: EquipmentResponse, onSaved: @escaping (EquipmentResponse) -> Void) {
        self.existing = existing
        self.onSaved = onSaved
        _name = State(initialValue: existing.name)
        _type = State(initialValue: existing.type)
        _frequency = State(initialValue: existing.frequency)
        _amount = State(initialValue: existing.amount)
        _affectsProductSafety = State(initialValue: existing.affectsProductSafety)
    }

    private var isValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty &&
        !frequency.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.hBackground.ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Basic info
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Основне")
                                .font(.headline)
                                .foregroundStyle(Color.hTextPrimary)

                            HaacpTextField("Назва обладнання *", text: $name)
                            HaacpTextField("Частота обслуговування *", text: $frequency)
                        }

                        // Type picker
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Тип")
                                .font(.headline)
                                .foregroundStyle(Color.hTextPrimary)

                            Picker("Тип обладнання", selection: $type) {
                                ForEach(EquipmentType.allCases, id: \.self) { t in
                                    Text(t.displayName).tag(t)
                                }
                            }
                            .pickerStyle(.segmented)
                        }

                        // Amount stepper
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Кількість")
                                .font(.headline)
                                .foregroundStyle(Color.hTextPrimary)

                            HStack {
                                Text("\(amount) од.")
                                    .font(.body)
                                    .foregroundStyle(Color.hTextPrimary)
                                Spacer()
                                Stepper("", value: $amount, in: 1...999)
                                    .labelsHidden()
                            }
                            .padding()
                            .background(Color.hSurface)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }

                        // Safety toggle
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Безпека")
                                .font(.headline)
                                .foregroundStyle(Color.hTextPrimary)

                            Toggle(isOn: $affectsProductSafety) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Впливає на безпеку продукту")
                                        .font(.subheadline)
                                        .foregroundStyle(Color.hTextPrimary)
                                    Text("Потраплятиме у панель уваги")
                                        .font(.caption)
                                        .foregroundStyle(Color.hTextSecondary)
                                }
                            }
                            .tint(Color.hAccent)
                            .padding()
                            .background(Color.hSurface)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }

                        if let error = errorMessage {
                            Text(error)
                                .font(.caption)
                                .foregroundStyle(Color.hDeviationRed)
                                .multilineTextAlignment(.center)
                        }

                        HaacpButton(existing == nil ? "Додати обладнання" : "Зберегти зміни", isLoading: isSaving) {
                            await save()
                        }
                        .opacity(isValid ? 1 : 0.5)
                        .disabled(!isValid)
                    }
                    .padding()
                }
            }
            .navigationTitle(existing == nil ? "Нове обладнання" : "Редагувати")
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
            let saved: EquipmentResponse
            if let existing {
                let body = EquipmentUpdateRequest(
                    type: type,
                    name: name.trimmingCharacters(in: .whitespaces),
                    frequency: frequency.trimmingCharacters(in: .whitespaces),
                    amount: amount,
                    affectsProductSafety: affectsProductSafety
                )
                saved = try await authStore.call { token in
                    try await APIClient.updateEquipment(orgId: orgId, equipmentId: existing.id, body: body, token: token)
                }
            } else {
                let body = EquipmentCreateRequest(
                    type: type,
                    name: name.trimmingCharacters(in: .whitespaces),
                    frequency: frequency.trimmingCharacters(in: .whitespaces),
                    amount: amount,
                    affectsProductSafety: affectsProductSafety
                )
                saved = try await authStore.call { token in
                    try await APIClient.createEquipment(orgId: orgId, body: body, token: token)
                }
            }
            onSaved(saved)
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}
