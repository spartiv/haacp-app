import SwiftUI

struct MedicalCheckFormView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    let existing: MedicalCheckResponse?
    let onSaved: (MedicalCheckResponse) -> Void

    @State private var employeeName: String
    @State private var nextCheckDate: Date

    @State private var isSaving = false
    @State private var errorMessage: String?

    private static let formatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    init(onSaved: @escaping (MedicalCheckResponse) -> Void) {
        self.existing = nil
        self.onSaved = onSaved
        _employeeName = State(initialValue: "")
        _nextCheckDate = State(initialValue: Date())
    }

    init(existing: MedicalCheckResponse, onSaved: @escaping (MedicalCheckResponse) -> Void) {
        self.existing = existing
        self.onSaved = onSaved
        _employeeName = State(initialValue: existing.employeeName)
        let parsed = Self.formatter.date(from: existing.nextCheckDate) ?? Date()
        _nextCheckDate = State(initialValue: parsed)
    }

    private var isValid: Bool {
        !employeeName.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.hBackground.ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Ім'я працівника")
                                .font(.headline).foregroundStyle(Color.hTextPrimary)
                            HaacpTextField("Ім'я та прізвище *", text: $employeeName)
                        }

                        VStack(alignment: .leading, spacing: 8) {
                            Text("Дата наступного огляду")
                                .font(.headline).foregroundStyle(Color.hTextPrimary)

                            DatePicker("", selection: $nextCheckDate, displayedComponents: .date)
                                .datePickerStyle(.compact)
                                .labelsHidden()
                                .environment(\.locale, Locale(identifier: "uk_UA"))
                                .padding(14)
                                .background(Color.hSurface)
                                .clipShape(RoundedRectangle(cornerRadius: 10))
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
                        }

                        if let error = errorMessage {
                            Text(error).font(.caption).foregroundStyle(Color.hDeviationRed)
                        }

                        HaacpButton(existing == nil ? "Додати запис" : "Зберегти зміни", isLoading: isSaving) {
                            await save()
                        }
                        .opacity(isValid ? 1 : 0.5)
                        .disabled(!isValid)
                    }
                    .padding()
                }
            }
            .navigationTitle(existing == nil ? "Новий медогляд" : "Редагувати")
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
        let dateString = Self.formatter.string(from: nextCheckDate)
        let trimmedName = employeeName.trimmingCharacters(in: .whitespaces)
        do {
            let saved: MedicalCheckResponse
            if let existing {
                saved = try await authStore.call { token in
                    try await APIClient.updateMedicalCheck(orgId: orgId, checkId: existing.id, body: MedicalCheckUpdateRequest(
                        employeeName: trimmedName,
                        nextCheckDate: dateString
                    ), token: token)
                }
            } else {
                saved = try await authStore.call { token in
                    try await APIClient.createMedicalCheck(orgId: orgId, body: MedicalCheckCreateRequest(
                        employeeName: trimmedName,
                        nextCheckDate: dateString
                    ), token: token)
                }
            }
            onSaved(saved)
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}
