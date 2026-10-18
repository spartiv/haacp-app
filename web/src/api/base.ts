/** `/api/v1/organizations/{id}` — every domain resource lives under it. */
export const orgBase = (organizationId: string) => `/api/v1/organizations/${encodeURIComponent(organizationId)}`

export const seg = encodeURIComponent
