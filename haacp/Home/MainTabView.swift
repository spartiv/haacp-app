import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            Tab("Огляд", systemImage: "house.fill") {
                NavigationStack {
                    DashboardView()
                }
            }

            Tab("Довідники", systemImage: "folder.fill") {
                NavigationStack {
                    DirectoriesView()
                }
            }
        }
        .tint(.hAccent)
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return MainTabView()
        .environment(store)
}
