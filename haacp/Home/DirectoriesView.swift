import SwiftUI

struct DirectoriesView: View {
    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            List {
                Section("Журнал подій") {
                    NavigationLink(destination: EventLogView()) {
                        Label("Журнал подій", systemImage: "doc.text.fill")
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .listRowBackground(Color.hSurface)
                }

                Section("Обладнання") {
                    NavigationLink(destination: EquipmentListView()) {
                        Label("Обладнання", systemImage: "gearshape.2.fill")
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .listRowBackground(Color.hSurface)
                }

                Section("Довідники") {
                    NavigationLink(destination: ChemicalListView()) {
                        Label("Хімічні засоби", systemImage: "flask.fill")
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .listRowBackground(Color.hSurface)
                    NavigationLink(destination: WasteTypeListView()) {
                        Label("Типи відходів", systemImage: "trash.fill")
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .listRowBackground(Color.hSurface)

                    NavigationLink(destination: MedicalCheckListView()) {
                        Label("Медогляди", systemImage: "heart.text.clipboard.fill")
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .listRowBackground(Color.hSurface)

                    NavigationLink(destination: AllergenListView()) {
                        Label("Алергени", systemImage: "leaf.fill")
                            .foregroundStyle(Color.hTextPrimary)
                    }
                    .listRowBackground(Color.hSurface)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.hBackground)
        }
        .navigationTitle("Довідники")
    }
}

private struct DirectoryRow: View {
    let title: String
    let icon: String
    let available: Bool

    var body: some View {
        HStack {
            Label(title, systemImage: icon)
                .foregroundStyle(available ? Color.hTextPrimary : Color.hTextSecondary)
            Spacer()
            if available {
                Image(systemName: "chevron.right")
                    .foregroundStyle(Color.hTextSecondary)
                    .font(.caption)
            } else {
                Text("Незабаром")
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.hSurface)
                    .clipShape(Capsule())
            }
        }
        .listRowBackground(Color.hSurface)
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        DirectoriesView()
            .environment(store)
    }
}
