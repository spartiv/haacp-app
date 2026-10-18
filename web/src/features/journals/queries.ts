// Queries shared by the dashboard cards and the journal screens: one cache entry
// per resource, so a new record shows up everywhere without a reload.
import { useQuery } from '@tanstack/react-query'
import { batchKeys, listProducts } from '../../api/batches'
import { eventLogKeys, listEventEntries, listEventLogTypes } from '../../api/eventLogs'
import { listChemicals, listEquipment, listMedicalChecks, referenceKeys } from '../../api/references'

export function useEventLogTypes(orgId: string) {
  return useQuery({
    queryKey: eventLogKeys.types(orgId),
    queryFn: ({ signal }) => listEventLogTypes(orgId, signal),
    staleTime: 60 * 60 * 1000, // fixed catalogue, rarely changes
  })
}

export function useEventEntries(orgId: string, typeId: string | undefined) {
  return useQuery({
    queryKey: eventLogKeys.entries(orgId, typeId ?? ''),
    queryFn: ({ signal }) => listEventEntries(orgId, typeId ?? '', signal),
    enabled: typeId !== undefined,
  })
}

/** Latest entry of one built-in event log (e.g. "glass", "eq"); null when there are none. */
export function useLatestEventEntry(orgId: string, typeKey: string) {
  const types = useEventLogTypes(orgId)
  const typeId = types.data?.find((type) => type.key === typeKey)?.id
  const entries = useEventEntries(orgId, typeId)
  return {
    isPending: types.isPending || (typeId !== undefined && entries.isPending),
    isError: types.isError || entries.isError,
    entry: entries.data?.[0] ?? null,
  }
}

export function useMedicalChecks(orgId: string) {
  return useQuery({
    queryKey: referenceKeys.medicalChecks(orgId),
    queryFn: ({ signal }) => listMedicalChecks(orgId, signal),
  })
}

export function useEquipment(orgId: string) {
  return useQuery({
    queryKey: referenceKeys.equipment(orgId),
    queryFn: ({ signal }) => listEquipment(orgId, signal),
  })
}

export function useChemicals(orgId: string) {
  return useQuery({
    queryKey: referenceKeys.chemicals(orgId),
    queryFn: ({ signal }) => listChemicals(orgId, signal),
  })
}

export function useProducts(orgId: string) {
  return useQuery({
    queryKey: batchKeys.products(orgId),
    queryFn: ({ signal }) => listProducts(orgId, signal),
  })
}
