import SwiftUI

struct BatchDetailView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    let batch: BatchResponse
    let product: ProductResponse
    let onUpdated: (BatchResponse) -> Void
    let onDeleted: () -> Void

    @State private var showEdit = false
    @State private var showDeleteConfirm = false
    @State private var isDeleting = false
    @State private var currentBatch: BatchResponse
    @State private var errorMessage: String?

    init(batch: BatchResponse, product: ProductResponse, onUpdated: @escaping (BatchResponse) -> Void, onDeleted: @escaping () -> Void) {
        self.batch = batch
        self.product = product
        self.onUpdated = onUpdated
        self.onDeleted = onDeleted
        _currentBatch = State(initialValue: batch)
    }

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    infoCard
                    if currentBatch.hasDeviation { deviationCard }
                    answersCard
                }
                .padding()
            }
        }
        .navigationTitle("Партія №\(currentBatch.number)")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button { showEdit = true } label: {
                        Label("Редагувати", systemImage: "pencil")
                    }
                    Button(role: .destructive) { showDeleteConfirm = true } label: {
                        Label("Видалити", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundStyle(Color.hAccent)
                }
            }
        }
        .navigationDestination(isPresented: $showEdit) {
            BatchRecordView(product: product, existing: currentBatch) { updated in
                currentBatch = updated
                onUpdated(updated)
                showEdit = false
            }
        }
        .confirmationDialog("Видалити партію?", isPresented: $showDeleteConfirm, titleVisibility: .visible) {
            Button("Видалити", role: .destructive) { Task { await deleteBatch() } }
            Button("Скасувати", role: .cancel) {}
        } message: {
            Text("Партію №\(currentBatch.number) буде видалено. Цю дію неможливо скасувати.")
        }
        .alert("Помилка", isPresented: Binding(get: { errorMessage != nil }, set: { if !$0 { errorMessage = nil } })) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    // MARK: - Cards

    private var infoCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Інформація", systemImage: "info.circle")
                .font(.headline)
                .foregroundStyle(Color.hTextPrimary)

            InfoRow(label: "Номер", value: currentBatch.number)
            if let name = currentBatch.name { InfoRow(label: "Назва", value: name) }
            InfoRow(label: "Дата виробництва", value: currentBatch.productionDate)
            InfoRow(label: "Статус", value: currentBatch.hasDeviation ? "Відхилення" : "Норма")
        }
        .padding()
        .background(Color.hSurface)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private var deviationCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Відхилення", systemImage: "exclamationmark.triangle.fill")
                .font(.headline)
                .foregroundStyle(Color.hDeviationRed)

            if let note = currentBatch.deviationNote, !note.isEmpty {
                InfoRow(label: "Опис", value: note)
            }
            if let action = currentBatch.correctiveAction, !action.isEmpty {
                InfoRow(label: "Корегувальні дії", value: action)
            }
        }
        .padding()
        .background(Color.hDeviationRed.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.hDeviationRed.opacity(0.3)))
    }

    private var answersCard: some View {
        let yesCount = currentBatch.answers.filter { $0.answer }.count
        let noCount = currentBatch.answers.filter { !$0.answer }.count
        return VStack(alignment: .leading, spacing: 12) {
            Label("Відповіді чеклисту", systemImage: "checklist")
                .font(.headline)
                .foregroundStyle(Color.hTextPrimary)

            HStack(spacing: 16) {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill").foregroundStyle(Color.hAccent)
                    Text("Так: \(yesCount)").font(.subheadline).foregroundStyle(Color.hTextPrimary)
                }
                HStack(spacing: 6) {
                    Image(systemName: "xmark.circle.fill").foregroundStyle(Color.hDeviationRed)
                    Text("Ні: \(noCount)").font(.subheadline).foregroundStyle(Color.hTextPrimary)
                }
                Spacer()
                Text("Всього: \(currentBatch.answers.count)")
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
            }
        }
        .padding()
        .background(Color.hSurface)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    // MARK: - Delete

    private func deleteBatch() async {
        guard let orgId = authStore.organizationId else { return }
        isDeleting = true
        defer { isDeleting = false }
        do {
            try await authStore.call { token in
                try await APIClient.deleteBatch(orgId: orgId, batchId: currentBatch.id, token: token)
            }
            onDeleted()
            dismiss()
        } catch {
            errorMessage = (error as? HaacpError)?.errorDescription ?? error.localizedDescription
        }
    }
}

private struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack(alignment: .top) {
            Text(label)
                .font(.caption)
                .foregroundStyle(Color.hTextSecondary)
                .frame(width: 120, alignment: .leading)
            Text(value)
                .font(.subheadline)
                .foregroundStyle(Color.hTextPrimary)
            Spacer()
        }
    }
}
