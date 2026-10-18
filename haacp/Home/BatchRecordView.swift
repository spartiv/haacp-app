import SwiftUI

struct BatchRecordView: View {
    @Environment(AuthStore.self) private var authStore
    let product: ProductResponse
    let existing: BatchResponse?
    let onSaved: (BatchResponse) -> Void

    @State private var checklistItems: [ChecklistItemResponse] = []
    @State private var isLoadingChecklist = true
    @State private var answers: [String: Bool]

    @State private var batchNumber: String
    @State private var batchName: String
    @State private var productionDate: Date
    @State private var deviationNote: String
    @State private var correctiveAction: String

    @State private var isSaving = false
    @State private var errorMessage: String?

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    init(product: ProductResponse, onSaved: @escaping (BatchResponse) -> Void) {
        self.product = product
        self.existing = nil
        self.onSaved = onSaved
        _batchNumber = State(initialValue: "")
        _batchName = State(initialValue: "")
        _productionDate = State(initialValue: Date())
        _deviationNote = State(initialValue: "")
        _correctiveAction = State(initialValue: "")
        _answers = State(initialValue: [:])
    }

    init(product: ProductResponse, existing: BatchResponse, onSaved: @escaping (BatchResponse) -> Void) {
        self.product = product
        self.existing = existing
        self.onSaved = onSaved
        _batchNumber = State(initialValue: existing.number)
        _batchName = State(initialValue: existing.name ?? "")
        _deviationNote = State(initialValue: existing.deviationNote ?? "")
        _correctiveAction = State(initialValue: existing.correctiveAction ?? "")
        _productionDate = State(initialValue: Self.dateFormatter.date(from: existing.productionDate) ?? Date())
        var initialAnswers: [String: Bool] = [:]
        for ans in existing.answers { initialAnswers[ans.checklistItemId] = ans.answer }
        _answers = State(initialValue: initialAnswers)
    }

    private var hasDeviation: Bool { answers.values.contains(false) }

    private var allAnswered: Bool {
        checklistItems.isEmpty || checklistItems.allSatisfy { answers[$0.id] != nil }
    }

    private var canSubmit: Bool {
        !batchNumber.trimmingCharacters(in: .whitespaces).isEmpty && allAnswered && !isSaving
    }

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoadingChecklist {
                ProgressView("Завантаження чеклисту...").tint(Color.hAccent)
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        batchInfoSection
                        if !checklistItems.isEmpty { checklistSection }
                        if hasDeviation { deviationSection }

                        if let error = errorMessage {
                            Text(error)
                                .font(.caption)
                                .foregroundStyle(.red)
                                .multilineTextAlignment(.center)
                        }

                        HaacpButton(existing == nil ? "Зберегти партію" : "Оновити партію", isLoading: isSaving) {
                            await saveBatch()
                        }
                        .opacity(canSubmit ? 1 : 0.5)
                        .disabled(!canSubmit)
                    }
                    .padding(16)
                }
            }
        }
        .navigationTitle(existing == nil ? "Нова партія" : "Редагувати партію")
#if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
#endif
        .task { await loadChecklist() }
    }

    private var batchInfoSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Інформація про партію")
                .font(.headline).foregroundStyle(Color.hTextPrimary)

            HaacpTextField("Номер партії *", text: $batchNumber)
            HaacpTextField("Назва (необов'язково)", text: $batchName)

            VStack(alignment: .leading, spacing: 6) {
                Text("Дата виробництва")
                    .font(.caption).foregroundStyle(Color.hTextSecondary)
                DatePicker("", selection: $productionDate, displayedComponents: .date)
                    .datePickerStyle(.compact)
                    .labelsHidden()
                    .environment(\.locale, Locale(identifier: "uk_UA"))
                    .padding(14)
                    .background(Color.hSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
            }
        }
    }

    private var checklistSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Контрольний список")
                .font(.headline).foregroundStyle(Color.hTextPrimary)

            ForEach(checklistItems.sorted { $0.position < $1.position }) { item in
                ChecklistItemRow(
                    item: item,
                    answer: Binding(
                        get: { answers[item.id] },
                        set: { answers[item.id] = $0 }
                    )
                )
            }
        }
    }

    private var deviationSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Виявлено відхилення", systemImage: "exclamationmark.triangle.fill")
                .font(.headline).foregroundStyle(Color.hDeviationRed)

            VStack(alignment: .leading, spacing: 4) {
                Text("Опис відхилення")
                    .font(.caption).foregroundStyle(Color.hTextSecondary)
                TextEditor(text: $deviationNote)
                    .frame(minHeight: 80)
                    .padding(10)
                    .background(Color.hSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Корегувальні дії")
                    .font(.caption).foregroundStyle(Color.hTextSecondary)
                TextEditor(text: $correctiveAction)
                    .frame(minHeight: 80)
                    .padding(10)
                    .background(Color.hSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.hAccent.opacity(0.3)))
            }
        }
    }

    private func loadChecklist() async {
        guard let orgId = authStore.organizationId else {
            isLoadingChecklist = false
            errorMessage = HaacpError.unauthorized.errorDescription
            return
        }
        do {
            checklistItems = try await authStore.call { token in
                try await APIClient.listChecklistItems(orgId: orgId, productId: product.id, token: token)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoadingChecklist = false
    }

    private func saveBatch() async {
        guard let orgId = authStore.organizationId else {
            errorMessage = HaacpError.unauthorized.errorDescription
            return
        }
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }

        let dateString = Self.dateFormatter.string(from: productionDate)

        let answersPayload = checklistItems.compactMap { item -> BatchAnswerInput? in
            guard let ans = answers[item.id] else { return nil }
            return BatchAnswerInput(checklistItemId: item.id, answer: ans)
        }

        let trimmedNumber = batchNumber.trimmingCharacters(in: .whitespaces)
        let trimmedName: String? = batchName.trimmingCharacters(in: .whitespaces).isEmpty ? nil : batchName.trimmingCharacters(in: .whitespaces)
        let note: String? = hasDeviation && !deviationNote.isEmpty ? deviationNote : nil
        let action: String? = hasDeviation && !correctiveAction.isEmpty ? correctiveAction : nil

        do {
            let batch: BatchResponse
            if let existing {
                let body = BatchUpdateRequest(
                    number: trimmedNumber,
                    name: trimmedName,
                    productionDate: dateString,
                    answers: answersPayload,
                    deviationNote: note,
                    correctiveAction: action
                )
                batch = try await authStore.call { token in
                    try await APIClient.updateBatch(orgId: orgId, batchId: existing.id, body: body, token: token)
                }
            } else {
                let body = BatchCreateRequest(
                    number: trimmedNumber,
                    name: trimmedName,
                    productionDate: dateString,
                    answers: answersPayload,
                    deviationNote: note,
                    correctiveAction: action
                )
                batch = try await authStore.call { token in
                    try await APIClient.recordBatch(orgId: orgId, productId: product.id, body: body, token: token)
                }
            }
            onSaved(batch)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct ChecklistItemRow: View {
    let item: ChecklistItemResponse
    @Binding var answer: Bool?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(item.label)
                .font(.body).foregroundStyle(Color.hTextPrimary)

            HStack(spacing: 12) {
                AnswerButton(label: "Так", isSelected: answer == true, isPositive: true) { answer = true }
                AnswerButton(label: "Ні", isSelected: answer == false, isPositive: false) { answer = false }
                Spacer()
            }
        }
        .padding(14)
        .background(Color.hSurface)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(answer == false ? Color.hDeviationRed.opacity(0.6) : Color.hAccent.opacity(0.2))
        )
    }
}

struct AnswerButton: View {
    let label: String
    let isSelected: Bool
    let isPositive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.subheadline.bold())
                .padding(.horizontal, 24)
                .padding(.vertical, 8)
                .background(isSelected ? (isPositive ? Color.hAccent : Color.hDeviationRed) : Color.hBackground)
                .foregroundStyle(isSelected ? .white : Color.hTextSecondary)
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    let product = ProductResponse(id: UUID().uuidString, organizationId: "org", name: "Молоко 2.5%")
    return NavigationStack {
        BatchRecordView(product: product) { _ in }
            .environment(store)
    }
}
