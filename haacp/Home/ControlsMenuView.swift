import SwiftUI

struct ControlsMenuView: View {
    @State private var period: ControlPeriod?

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()

            VStack(spacing: 16) {
                ControlMenuCard(
                    title: "Щоденний контроль",
                    subtitle: "Заповніть контроль за сьогодні",
                    icon: "sun.max.fill"
                ) {
                    period = .daily
                }

                ControlMenuCard(
                    title: "Місячний контроль",
                    subtitle: "Заповніть контроль за цей місяць",
                    icon: "calendar"
                ) {
                    period = .monthly
                }

                Spacer()
            }
            .padding()
        }
        .navigationTitle("Контроль")
        .navigationDestination(item: $period) { p in
            ControlRecordView(period: p)
        }
    }
}

private struct ControlMenuCard: View {
    let title: String
    let subtitle: String
    let icon: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(Color.hAccent)
                    .frame(width: 36)

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.headline)
                        .foregroundStyle(Color.hTextPrimary)
                    Text(subtitle)
                        .font(.subheadline)
                        .foregroundStyle(Color.hTextSecondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundStyle(Color.hTextSecondary)
            }
            .padding()
            .background(Color.hSurface)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        ControlsMenuView()
            .environment(store)
    }
}
