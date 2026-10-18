import SwiftUI

@main
struct haacpApp: App {
    @State private var authStore = AuthStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(authStore)
        }
    }
}
