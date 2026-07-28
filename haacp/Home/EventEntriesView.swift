import SwiftUI

struct EventEntriesView: View {
    @Environment(AuthStore.self) private var authStore

    let logType: EventLogTypeResponse

    @State private var entries: [EventEntryResponse] = []
    @State private var isLoading = false
    @State private var showAddForm = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && entries.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else if entries.isEmpty {
                VStack(spacing: 16) {
                    Text(logType.iconLabel)
                        .font(.system(size: 52))
                    Text("Записів немає")
                        .foregroundStyle(Color.hTextSecondary)
                    Button { showAddForm = true } label: {
                        Text("Додати перший запис").foregroundStyle(Color.hAccent)
                    }
                }
            } else {
                List {
                    ForEach(entries) { entry in
                        EntryRow(entry: entry, schema: logType.logSchema)
                            .listRowBackground(Color.hSurface)
                    }
                    .onDelete { indexSet in
                        Task { await deleteEntries(at: indexSet) }
                    }
                }
                .scrollContentBackground(.hidden)
                .refreshable { await load() }
            }
        }
        .navigationTitle(logType.name)
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
            EventEntryFormView(logType: logType) { entry in
                entries.insert(entry, at: 0)
                showAddForm = false
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
            entries = try await authStore.call { token in
                try await APIClient.listEventEntries(orgId: orgId, typeId: logType.id, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func deleteEntries(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let entry = entries[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteEventEntry(orgId: orgId, entryId: entry.id, token: token)
                }
                entries.remove(at: index)
            } catch {
                errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
            }
        }
    }
}

private struct EntryRow: View {
    let entry: EventEntryResponse
    let schema: EventLogSchema

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    Text(entry.entryDate)
                        .font(.headline)
                        .foregroundStyle(Color.hTextPrimary)
                    if entry.hasDeviation {
                        Label("Відхилення", systemImage: "exclamationmark.triangle.fill")
                            .font(.caption)
                            .foregroundStyle(Color.hDeviationRed)
                    }
                }
                Text(payloadSummary)
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }

    private var payloadSummary: String {
        let p = entry.payload
        switch schema {
        case .standard:
            return p.details ?? "—"
        case .water:
            let paramsStr = p.params?.joined(separator: ", ") ?? "—"
            let resultStr = p.result == "ok" ? "Норма" : "Відхилення"
            return "\(paramsStr) · \(resultStr)"
        case .pests:
            let detected = p.detected == "yes" ? "Виявлено" : "Не виявлено"
            return detected + (p.actions.map { " · \($0)" } ?? "")
        }
    }
}
