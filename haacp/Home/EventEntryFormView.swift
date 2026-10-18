import SwiftUI

private let waterParamOptions = ["pH", "Хлор", "Мутність", "Мікробіологія", "Твердість"]

struct EventEntryFormView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    let logType: EventLogTypeResponse
    let onSaved: (EventEntryResponse) -> Void

    @State private var entryDate = Date()

    // standard
    @State private var details = ""

    // water
    @State private var selectedParams: Set<String> = []
    @State private var waterResult = "ok"

    // pests
    @State private var pestsDetected = false
    @State private var pestsActions = ""

    @State private var isSaving = false
    @State private var errorMessage: String?

    private var isValid: Bool {
        switch logType.logSchema {
        case .standard: return !details.trimmingCharacters(in: .whitespaces).isEmpty
        case .water:    return !selectedParams.isEmpty
        case .pests:    return !pestsActions.trimmingCharacters(in: .whitespaces).isEmpty
        }
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.hBackground.ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Date
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Дата")
                                .font(.headline)
                                .foregroundStyle(Color.hTextPrimary)

                            DatePicker("", selection: $entryDate, displayedComponents: .date)
                                .datePickerStyle(.compact)
                                .labelsHidden()
                                .environment(\.locale, Locale(identifier: "uk_UA"))
                                .padding(14)
                                .background(Color.hSurface)
                                .clipShape(RoundedRectangle(cornerRadius: 10))
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
                        }

                        // Schema-specific fields
                        switch logType.logSchema {
                        case .standard: standardFields
                        case .water:    waterFields
                        case .pests:    pestsFields
                        }

                        if let error = errorMessage {
                            Text(error)
                                .font(.caption)
                                .foregroundStyle(Color.hDeviationRed)
                                .multilineTextAlignment(.center)
                        }

                        HaacpButton("Зберегти запис", isLoading: isSaving) {
                            await save()
                        }
                        .opacity(isValid ? 1 : 0.5)
                        .disabled(!isValid)
                    }
                    .padding()
                }
            }
            .navigationTitle(logType.name)
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

    // MARK: - Schema fields

    private var standardFields: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Деталі")
                .font(.headline)
                .foregroundStyle(Color.hTextPrimary)

            TextEditor(text: $details)
                .frame(minHeight: 120)
                .padding(10)
                .background(Color.hSurface)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
        }
    }

    private var waterFields: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Text("Показники")
                    .font(.headline)
                    .foregroundStyle(Color.hTextPrimary)

                VStack(spacing: 0) {
                    ForEach(waterParamOptions, id: \.self) { param in
                        Toggle(param, isOn: Binding(
                            get: { selectedParams.contains(param) },
                            set: { selected in
                                if selected { selectedParams.insert(param) }
                                else { selectedParams.remove(param) }
                            }
                        ))
                        .tint(Color.hAccent)
                        .padding(.horizontal)
                        .padding(.vertical, 10)
                        .background(Color.hSurface)
                        if param != waterParamOptions.last {
                            Divider().padding(.leading)
                        }
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Результат")
                    .font(.headline)
                    .foregroundStyle(Color.hTextPrimary)

                Picker("Результат", selection: $waterResult) {
                    Text("Норма").tag("ok")
                    Text("Відхилення").tag("deviation")
                }
                .pickerStyle(.segmented)
            }
        }
    }

    private var pestsFields: some View {
        VStack(alignment: .leading, spacing: 16) {
            Toggle(isOn: $pestsDetected) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Виявлено шкідників")
                        .font(.headline)
                        .foregroundStyle(Color.hTextPrimary)
                    Text(pestsDetected ? "Так" : "Ні")
                        .font(.caption)
                        .foregroundStyle(pestsDetected ? Color.hDeviationRed : Color.hTextSecondary)
                }
            }
            .tint(Color.hDeviationRed)
            .padding()
            .background(Color.hSurface)
            .clipShape(RoundedRectangle(cornerRadius: 10))

            VStack(alignment: .leading, spacing: 8) {
                Text("Вжиті заходи")
                    .font(.headline)
                    .foregroundStyle(Color.hTextPrimary)

                TextEditor(text: $pestsActions)
                    .frame(minHeight: 100)
                    .padding(10)
                    .background(Color.hSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
            }
        }
    }

    // MARK: - Save

    private func save() async {
        guard let orgId = authStore.organizationId else {
            errorMessage = HaacpError.unauthorized.errorDescription
            return
        }
        isSaving = true
        defer { isSaving = false }

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateString = formatter.string(from: entryDate)

        let payload: EventPayload
        switch logType.logSchema {
        case .standard:
            payload = .standard(details: details.trimmingCharacters(in: .whitespaces))
        case .water:
            payload = .water(params: Array(selectedParams), result: waterResult)
        case .pests:
            payload = .pests(
                detected: pestsDetected ? "yes" : "no",
                actions: pestsActions.trimmingCharacters(in: .whitespaces)
            )
        }

        do {
            let body = EventEntryCreateRequest(entryDate: dateString, payload: payload)
            let entry = try await authStore.call { token in
                try await APIClient.createEventEntry(orgId: orgId, typeId: logType.id, body: body, token: token)
            }
            onSaved(entry)
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}
