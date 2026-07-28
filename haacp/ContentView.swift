import SwiftUI

struct ContentView: View {
    @Environment(AuthStore.self) private var authStore

    var body: some View {
        if authStore.isAuthenticated {
            MainTabView()
        } else {
            LoginView()
        }
    }
}
