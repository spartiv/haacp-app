import { orgBase, seg } from './base'
import { apiRequest } from './client'
import type { Batch, BatchCreate, Product, ProductChecklistItem } from './types'

export const batchKeys = {
  products: (organizationId: string) => ['products', organizationId] as const,
  checklist: (organizationId: string, productId: string) => ['products', organizationId, productId, 'checklist'] as const,
  batches: (organizationId: string, productId: string) => ['batches', organizationId, productId] as const,
  allBatches: (organizationId: string) => ['batches', organizationId] as const,
}

export function listProducts(organizationId: string, signal?: AbortSignal): Promise<Product[]> {
  return apiRequest<Product[]>(`${orgBase(organizationId)}/products`, { signal })
}

export function createProduct(organizationId: string, name: string): Promise<Product> {
  return apiRequest<Product>(`${orgBase(organizationId)}/products`, { method: 'POST', body: { name } })
}

export function deleteProduct(organizationId: string, productId: string): Promise<void> {
  return apiRequest<void>(`${orgBase(organizationId)}/products/${seg(productId)}`, { method: 'DELETE' })
}

export function listProductChecklist(
  organizationId: string,
  productId: string,
  signal?: AbortSignal,
): Promise<ProductChecklistItem[]> {
  return apiRequest<ProductChecklistItem[]>(`${orgBase(organizationId)}/products/${seg(productId)}/checklist-items`, {
    signal,
  })
}

export function createProductChecklistItem(
  organizationId: string,
  productId: string,
  label: string,
): Promise<ProductChecklistItem> {
  return apiRequest<ProductChecklistItem>(`${orgBase(organizationId)}/products/${seg(productId)}/checklist-items`, {
    method: 'POST',
    body: { label },
  })
}

export function deleteProductChecklistItem(organizationId: string, productId: string, itemId: string): Promise<void> {
  return apiRequest<void>(
    `${orgBase(organizationId)}/products/${seg(productId)}/checklist-items/${seg(itemId)}`,
    { method: 'DELETE' },
  )
}

/** Newest production date first. */
export function listBatches(organizationId: string, productId: string, signal?: AbortSignal): Promise<Batch[]> {
  return apiRequest<Batch[]>(`${orgBase(organizationId)}/products/${seg(productId)}/batches`, { signal })
}

export function createBatch(organizationId: string, productId: string, body: BatchCreate): Promise<Batch> {
  return apiRequest<Batch>(`${orgBase(organizationId)}/products/${seg(productId)}/batches`, { method: 'POST', body })
}

export function deleteBatch(organizationId: string, batchId: string): Promise<void> {
  return apiRequest<void>(`${orgBase(organizationId)}/batches/${seg(batchId)}`, { method: 'DELETE' })
}
