import SwiftUI

struct SignupView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var email = ""
    @State private var password = ""
    @State private var fullName = ""
    @State private var organizationName = ""
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            ScrollView {
                VStack(spacing: 24) {
                    VStack(spacing: 8) {
                        Text("Реєстрація")
                            .font(.largeTitle.bold())
                            .foregroundStyle(Color.hTextPrimary)
                        Text("Створіть акаунт вашого підприємства")
                            .font(.subheadline)
                            .foregroundStyle(Color.hTextSecondary)
                    }
                    .padding(.top, 32)

                    VStack(spacing: 16) {
                        HaacpTextField("Ім'я та прізвище", text: $fullName)
#if os(iOS)
                            .textContentType(.name)
#endif

                        HaacpTextField("Назва підприємства", text: $organizationName)
                            .autocorrectionDisabled()

                        HaacpTextField("Електронна пошта", text: $email)
                            .autocorrectionDisabled()
#if os(iOS)
                            .keyboardType(.emailAddress)
                            .textContentType(.emailAddress)
                            .textInputAutocapitalization(.never)
#endif

                        HaacpSecureField("Пароль (мін. 8 символів)", text: $password)
#if os(iOS)
                            .textContentType(.newPassword)
#endif
                    }

                    if let error = errorMessage {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    HaacpButton("Зареєструватись", isLoading: isLoading) {
                        await signup()
                    }

                    Spacer().frame(height: 40)
                }
                .padding(.horizontal, 24)
            }
        }
#if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
#endif
    }

    private func signup() async {
        let trimmedEmail = email.lowercased().trimmingCharacters(in: .whitespaces)
        let trimmedName = fullName.trimmingCharacters(in: .whitespaces)
        let trimmedOrg = organizationName.trimmingCharacters(in: .whitespaces)
        guard !trimmedEmail.isEmpty, !password.isEmpty, !trimmedName.isEmpty, !trimmedOrg.isEmpty else {
            errorMessage = "Заповніть усі поля"
            return
        }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            try await authStore.signup(
                email: trimmedEmail,
                password: password,
                fullName: trimmedName,
                organizationName: trimmedOrg
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        SignupView()
            .environment(AuthStore())
    }
}
