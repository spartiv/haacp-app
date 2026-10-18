import SwiftUI

struct LoginView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showSignup = false

    var body: some View {
        NavigationStack {
            ZStack {
                Color.hBackground.ignoresSafeArea()

                VStack(spacing: 32) {
                    VStack(spacing: 8) {
                        Text("Polton HACCP")
                            .font(.largeTitle.bold())
                            .foregroundStyle(Color.hTextPrimary)
                        Text("Система контролю якості")
                            .font(.subheadline)
                            .foregroundStyle(Color.hTextSecondary)
                    }
                    .padding(.top, 64)

                    VStack(spacing: 16) {
                        HaacpTextField("Електронна пошта", text: $email)
                            .autocorrectionDisabled()
#if os(iOS)
                            .keyboardType(.emailAddress)
                            .textContentType(.emailAddress)
                            .textInputAutocapitalization(.never)
#endif

                        HaacpSecureField("Пароль", text: $password)
#if os(iOS)
                            .textContentType(.password)
#endif
                    }

                    if let error = errorMessage {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    VStack(spacing: 12) {
                        HaacpButton("Увійти", isLoading: isLoading) {
                            await login()
                        }

                        Button("Зареєструватись") {
                            showSignup = true
                        }
                        .foregroundStyle(Color.hAccent)
                    }

                    Spacer()
                }
                .padding(.horizontal, 24)
            }
            .navigationDestination(isPresented: $showSignup) {
                SignupView()
            }
        }
    }

    private func login() async {
        guard !email.isEmpty, !password.isEmpty else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            try await authStore.login(
                email: email.lowercased().trimmingCharacters(in: .whitespaces),
                password: password
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    LoginView()
        .environment(AuthStore())
}
