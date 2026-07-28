import SwiftUI

struct HomeView: View {
    @Environment(AuthStore.self) private var authStore

    @State private var products: [ProductResponse] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showAddProduct = false
    @State private var newProductName = ""

    var body: some View {
        ZStack {
            Color.hBackground.ignoresSafeArea()
            content
        }
        .navigationTitle("Продукти")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showAddProduct = true } label: {
                    Image(systemName: "plus").foregroundStyle(Color.hAccent)
                }
            }
        }
        .alert("Новий продукт", isPresented: $showAddProduct) {
            TextField("Назва продукту", text: $newProductName)
            Button("Скасувати", role: .cancel) { newProductName = "" }
            Button("Додати") { Task { await addProduct() } }
        }
        .task { await loadProducts() }
    }

    @ViewBuilder
    private var content: some View {
        if isLoading && products.isEmpty {
            ProgressView("Завантаження...").tint(Color.hAccent)
        } else if products.isEmpty {
            VStack(spacing: 16) {
                Image(systemName: "shippingbox")
                    .font(.system(size: 48))
                    .foregroundStyle(Color.hAccent.opacity(0.5))
                Text("Продукти відсутні")
                    .foregroundStyle(Color.hTextSecondary)
                Text("Натисніть + щоб додати перший продукт")
                    .font(.caption)
                    .foregroundStyle(Color.hTextSecondary)
            }
        } else {
            List {
                ForEach(products) { product in
                    NavigationLink(destination: ProductDetailView(product: product)) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(product.name)
                                .font(.headline)
                                .foregroundStyle(Color.hTextPrimary)
                            Text("Переглянути партії та чеклист")
                                .font(.caption)
                                .foregroundStyle(Color.hTextSecondary)
                        }
                        .padding(.vertical, 4)
                    }
                    .listRowBackground(Color.hSurface)
                }
                .onDelete { indexSet in
                    Task { await deleteProducts(at: indexSet) }
                }
            }
            .scrollContentBackground(.hidden)
            .refreshable { await loadProducts() }
        }
    }

    private func loadProducts() async {
        guard let orgId = authStore.organizationId else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            products = try await authStore.call { token in
                try await APIClient.listProducts(orgId: orgId, token: token)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func addProduct() async {
        guard let orgId = authStore.organizationId else { return }
        let name = newProductName.trimmingCharacters(in: .whitespaces)
        newProductName = ""
        guard !name.isEmpty else { return }
        do {
            let product = try await authStore.call { token in
                try await APIClient.createProduct(orgId: orgId, name: name, token: token)
            }
            products.append(product)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func deleteProducts(at indexSet: IndexSet) async {
        guard let orgId = authStore.organizationId else { return }
        for index in indexSet {
            let product = products[index]
            do {
                try await authStore.call { token in
                    try await APIClient.deleteProduct(orgId: orgId, productId: product.id, token: token)
                }
                products.remove(at: index)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}

#Preview("Empty state") {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack { HomeView().environment(store) }
}

#Preview("With products") {
    let store = AuthStore()
    store.setupForPreview()
    return NavigationStack {
        HomeView().environment(store)
    }
}
