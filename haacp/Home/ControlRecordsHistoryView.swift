import SwiftUI

struct ControlRecordsHistoryView: View {
    @Environment(AuthStore.self) private var authStore

    let period: ControlPeriod

    @State private var records: [ControlRecordResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var editingRecord: ControlRecordResponse?
    @State private var showEdit = false

    private static let inputFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    private static let displayFormatterDaily: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "d MMM yyyy"
        f.locale = Locale(identifier: "uk_UA")
        return f
    }()

    private static let displayFormatterMonthly: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "LLLL yyyy"
        f.locale = Locale(identifier: "uk_UA")
        return f
    }()

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()
            content
        }
        .navigationTitle("Записи")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .navigationDestination(isPresented: $showEdit) {
            if let record = editingRecord {
                ControlRecordView(period: period, editing: record)
            }
        }
        .alert("Помилка", isPresented: Binding(get: { errorMessage != nil }, set: { if !$0 { errorMessage = nil } })) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task { await load() }
    }

    @ViewBuilder
    private var content: some View {
        if isLoading && records.isEmpty {
            ProgressView().tint(.hAccent)
        } else if records.isEmpty {
            VStack(spacing: 12) {
                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: 48))
                    .foregroundStyle(Color.hAccent.opacity(0.4))
                Text("Записів ще немає")
                    .foregroundStyle(Color.hTextSecondary)
            }
        } else {
            List {
                ForEach(records) { record in
                    Button {
                        editingRecord = record
                        showEdit = true
                    } label: {
                        RecordRow(record: record, period: period)
                    }
                    .listRowBackground(Color.hSurface)
                    .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                        Button(role: .destructive) {
                            Task { await delete(record) }
                        } label: {
                            Label("Видалити", systemImage: "trash")
                        }
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.hBackground)
            .refreshable { await load() }
        }
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let loaded = try await authStore.call { token in
                guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                return try await APIClient.listControlRecords(orgId: orgId, period: period, token: token)
            }
            records = loaded.sorted {
                ($0.periodDate) > ($1.periodDate)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func delete(_ record: ControlRecordResponse) async {
        do {
            try await authStore.call { token in
                guard let orgId = await authStore.organizationId else { throw HaacpError.unknown }
                try await APIClient.deleteControlRecord(orgId: orgId, recordId: record.id, token: token)
            }
            records.removeAll { $0.id == record.id }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}

// MARK: - Row

private struct RecordRow: View {
    let record: ControlRecordResponse
    let period: ControlPeriod

    private static let inputFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    private static let dailyFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "d MMM yyyy"
        f.locale = Locale(identifier: "uk_UA")
        return f
    }()

    private static let monthlyFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "LLLL yyyy"
        f.locale = Locale(identifier: "uk_UA")
        return f
    }()

    private var formattedDate: String {
        guard let date = Self.inputFormatter.date(from: record.periodDate) else {
            return record.periodDate
        }
        return period == .daily
            ? Self.dailyFormatter.string(from: date)
            : Self.monthlyFormatter.string(from: date)
    }

    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(record.hasDeviation ? Color.hDeviationRed : Color.green)
                .frame(width: 10, height: 10)

            VStack(alignment: .leading, spacing: 3) {
                Text(formattedDate)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(Color.hTextPrimary)

                if let note = record.note, !note.isEmpty {
                    Text(note)
                        .font(.caption)
                        .foregroundStyle(Color.hTextSecondary)
                        .lineLimit(1)
                }

                Text(record.hasDeviation ? "Відхилення" : "Норма")
                    .font(.caption)
                    .foregroundStyle(record.hasDeviation ? Color.hDeviationRed : Color.hTextSecondary)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color.hTextSecondary)
        }
        .padding(.vertical, 6)
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        ControlRecordsHistoryView(period: .daily)
            .environment(store)
    }
}
