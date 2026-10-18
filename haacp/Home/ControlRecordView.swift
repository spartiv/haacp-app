import SwiftUI

struct ControlRecordView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    let period: ControlPeriod
    // Non-nil when editing a specific past record by ID (PATCH); nil = fill/upsert current (PUT).
    let editingRecord: ControlRecordResponse?

    @State private var checklistItems: [ControlChecklistItemResponse] = []
    @State private var isLoadingItems = true

    @State private var answers: [String: Bool] = [:]
    @State private var periodDate: Date = Date()
    @State private var note: String = ""
    @State private var isSaving = false

    @State private var showAddQuestion = false
    @State private var newQuestionLabel = ""
    @State private var showHistory = false

    @State private var futureDateMessage: String?
    @State private var errorMessage: String?

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    init(period: ControlPeriod) {
        self.period = period
        self.editingRecord = nil
    }

    init(period: ControlPeriod, editing record: ControlRecordResponse) {
        self.period = period
        self.editingRecord = record
    }

    private var title: String {
        period == .daily ? "Щоденний контроль" : "Місячний контроль"
    }

    private var dateLabel: String {
        period == .daily ? "Дата контролю" : "Місяць контролю"
    }

    private var hasDeviation: Bool { answers.values.contains(false) }

    private var allAnswered: Bool {
        checklistItems.allSatisfy { answers[$0.id] != nil }
    }

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()
            content
        }
        .navigationTitle(editingRecord == nil ? title : "Редагувати запис")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                if editingRecord == nil {
                    Button {
                        showHistory = true
                    } label: {
                        Image(systemName: "clock.arrow.circlepath").foregroundStyle(Color.hAccent)
                    }
                }
                Button { showAddQuestion = true } label: {
                    Image(systemName: "plus").foregroundStyle(Color.hAccent)
                }
            }
        }
        .navigationDestination(isPresented: $showHistory) {
            ControlRecordsHistoryView(period: period)
        }
        .alert("Нове питання", isPresented: $showAddQuestion) {
            TextField("Текст питання", text: $newQuestionLabel)
            Button("Скасувати", role: .cancel) { newQuestionLabel = "" }
            Button("Додати") { Task { await addQuestion() } }
        }
        .alert("Помилка", isPresented: Binding(get: { errorMessage != nil }, set: { if !$0 { errorMessage = nil } })) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task { await loadChecklist() }
    }

    @ViewBuilder
    private var content: some View {
        if isLoadingItems {
            ProgressView().tint(.hAccent)
        } else if checklistItems.isEmpty {
            VStack(spacing: 16) {
                Image(systemName: "checklist")
                    .font(.system(size: 48))
                    .foregroundStyle(Color.hAccent.opacity(0.5))
                Text("Питань ще немає")
                    .foregroundStyle(Color.hTextSecondary)
                Button { showAddQuestion = true } label: {
                    Text("Додати перше питання").foregroundStyle(Color.hAccent)
                }
            }
        } else {
            List {
                // Date picker
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(dateLabel)
                            .font(.caption)
                            .foregroundStyle(Color.hTextSecondary)

                        DatePicker(
                            "",
                            selection: Binding(
                                get: { periodDate },
                                set: { periodDate = $0; futureDateMessage = nil }
                            ),
                            in: ...Date(),
                            displayedComponents: .date
                        )
                        .datePickerStyle(.compact)
                        .labelsHidden()
                        .environment(\.locale, Locale(identifier: "uk_UA"))

                        if let msg = futureDateMessage {
                            Text(msg)
                                .font(.caption)
                                .foregroundStyle(Color.hDeviationRed)
                        }
                    }
                    .padding(.vertical, 4)
                    .listRowBackground(Color.hSurface)
                }

                // Checklist items
                ForEach(checklistItems) { item in
                    ControlItemRow(
                        item: item,
                        answer: answers[item.id],
                        onAnswer: { answers[item.id] = $0 }
                    )
                    .listRowBackground(Color.hSurface)
                    .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                    .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                        Button(role: .destructive) {
                            Task { await deleteItem(item) }
                        } label: {
                            Label("Видалити", systemImage: "trash")
                        }
                    }
                }

                // Note field
                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Примітка")
                            .font(.caption)
                            .foregroundStyle(Color.hTextSecondary)
                        TextEditor(text: $note)
                            .frame(minHeight: 72)
                            .scrollContentBackground(.hidden)
                            .background(Color.clear)
                    }
                    .padding(.vertical, 4)
                    .listRowBackground(Color.hSurface)
                }

                if hasDeviation {
                    deviationBanner
                        .listRowBackground(Color.clear)
                        .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.hBackground)
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: 0) {
                    Divider()
                    HaacpButton(allAnswered ? "Зберегти" : "Дайте відповідь на всі питання", isLoading: isSaving) {
                        await save()
                    }
                    .disabled(!allAnswered)
                    .padding()
                    .background(Color.hBackground)
                }
            }
        }
    }

    private var deviationBanner: some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(Color.hDeviationRed)
            Text("Виявлено відхилення")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Color.hDeviationRed)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color.hDeviationRed.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Network

    private func loadChecklist() async {
        isLoadingItems = true
        defer { isLoadingItems = false }
        do {
            let items = try await authStore.call { token in
                guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                return try await APIClient.listControlChecklistItems(orgId: orgId, period: period, token: token)
            }
            checklistItems = items.sorted { $0.position < $1.position }

            if let record = editingRecord {
                // Editing mode: pre-fill directly from the provided record.
                if let date = Self.dateFormatter.date(from: record.periodDate) { periodDate = date }
                note = record.note ?? ""
                for answer in record.answers { answers[answer.controlChecklistItemId] = answer.answer }
            } else {
                // Fill-current mode: attempt to load today's record for pre-fill.
                do {
                    let record = try await authStore.call { token -> ControlRecordResponse in
                        guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                        return try await APIClient.getCurrentControl(orgId: orgId, period: period, token: token)
                    }
                    if let date = Self.dateFormatter.date(from: record.periodDate) { periodDate = date }
                    note = record.note ?? ""
                    for answer in record.answers { answers[answer.controlChecklistItemId] = answer.answer }
                } catch let e as HaacpError {
                    switch e {
                    case .api(let code, _) where code == "control_record_not_filled" || code == "control_record_not_found":
                        break
                    default:
                        throw e
                    }
                }
            }
        } catch let error as HaacpError {
            if case .api(let code, _) = error, code == "control_record_not_filled" {
                // No record yet — blank form
            } else {
                errorMessage = error.errorDescription
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func addQuestion() async {
        let label = newQuestionLabel.trimmingCharacters(in: .whitespaces)
        newQuestionLabel = ""
        guard !label.isEmpty else { return }
        do {
            let item = try await authStore.call { token in
                guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                return try await APIClient.addControlChecklistItem(orgId: orgId, period: period, label: label, token: token)
            }
            checklistItems.append(item)
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func deleteItem(_ item: ControlChecklistItemResponse) async {
        do {
            try await authStore.call { token in
                guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                try await APIClient.deleteControlChecklistItem(orgId: orgId, period: period, itemId: item.id, token: token)
            }
            checklistItems.removeAll { $0.id == item.id }
            answers.removeValue(forKey: item.id)
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func save() async {
        futureDateMessage = nil
        isSaving = true
        defer { isSaving = false }
        do {
            let inputs = checklistItems.compactMap { item -> ControlAnswerInput? in
                guard let answer = answers[item.id] else { return nil }
                return ControlAnswerInput(controlChecklistItemId: item.id, answer: answer)
            }
            let dateString = Self.dateFormatter.string(from: periodDate)
            let trimmedNote: String? = note.trimmingCharacters(in: .whitespaces).isEmpty
                ? nil
                : note.trimmingCharacters(in: .whitespaces)
            let body = ControlRecordUpsertRequest(answers: inputs, periodDate: dateString, note: trimmedNote)

            if let record = editingRecord {
                _ = try await authStore.call { token in
                    guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                    return try await APIClient.patchControlRecord(orgId: orgId, recordId: record.id, body: body, token: token)
                }
            } else {
                _ = try await authStore.call { token in
                    guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                    return try await APIClient.upsertCurrentControl(orgId: orgId, period: period, body: body, token: token)
                }
            }
            dismiss()
        } catch let e as HaacpError {
            if case .api(let code, _) = e, code == "future_period_date" {
                futureDateMessage = "Обрана дата знаходиться в майбутньому. Будь ласка, оберіть сьогодні або минулу дату."
            } else {
                errorMessage = e.errorDescription
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Sub-views

private struct ControlItemRow: View {
    let item: ControlChecklistItemResponse
    let answer: Bool?
    let onAnswer: (Bool) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(item.label)
                .font(.subheadline)
                .foregroundStyle(Color.hTextPrimary)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 12) {
                ControlAnswerButton(label: "Так", isSelected: answer == true, isDeviation: false) { onAnswer(true) }
                ControlAnswerButton(label: "Ні",  isSelected: answer == false, isDeviation: true)  { onAnswer(false) }
            }
        }
        .padding()
        .background(Color.hSurface)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

private struct ControlAnswerButton: View {
    let label: String
    let isSelected: Bool
    let isDeviation: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.subheadline.weight(.semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(isSelected ? (isDeviation ? Color.hDeviationRed : Color.hAccent) : Color.hBackground)
                .foregroundStyle(isSelected ? .white : Color.hTextSecondary)
                .clipShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        ControlRecordView(period: .daily)
            .environment(store)
    }
}
