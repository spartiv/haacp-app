import SwiftUI

struct EventLogView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var logTypes: [EventLogTypeResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            if isLoading && logTypes.isEmpty {
                ProgressView().tint(Color.hAccent)
            } else {
                List(logTypes.sorted { $0.position < $1.position }) { logType in
                    NavigationLink(destination: EventEntriesView(logType: logType)) {
                        HStack(spacing: 14) {
                            Text(logType.iconLabel)
                                .font(.title2)
                                .frame(width: 36, height: 36)
                                .background(Color.hAccent.opacity(0.12))
                                .clipShape(RoundedRectangle(cornerRadius: 8))

                            VStack(alignment: .leading, spacing: 3) {
                                Text(logType.name)
                                    .font(.headline)
                                    .foregroundStyle(Color.hTextPrimary)
                                Text(schemaLabel(logType.logSchema))
                                    .font(.caption)
                                    .foregroundStyle(Color.hTextSecondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .listRowBackground(Color.hSurface)
                }
                .scrollContentBackground(.hidden)
                .refreshable { await load() }
            }
        }
        .navigationTitle("Журнал подій")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
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
            logTypes = try await authStore.call { token in
                try await APIClient.listEventLogTypes(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func schemaLabel(_ schema: EventLogSchema) -> String {
        switch schema {
        case .standard: return "Довільний запис"
        case .water:    return "Аналіз води"
        case .pests:    return "Контроль шкідників"
        }
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        EventLogView().environment(store)
    }
}
