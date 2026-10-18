import { orgBase, seg } from './base'
import { apiDownload, apiRequest, type DownloadedFile } from './client'
import type {
  Attachment,
  Chemical,
  ChemicalCreate,
  ChemicalUpdate,
  Equipment,
  EquipmentCreate,
  EquipmentUpdate,
  MedicalCheck,
  MedicalCheckCreate,
  MedicalCheckUpdate,
} from './types'

export const referenceKeys = {
  equipment: (organizationId: string) => ['equipment', organizationId] as const,
  chemicals: (organizationId: string) => ['chemicals', organizationId] as const,
  medicalChecks: (organizationId: string) => ['medical-checks', organizationId] as const,
}

// ---- Equipment ----
export function listEquipment(organizationId: string, signal?: AbortSignal): Promise<Equipment[]> {
  return apiRequest<Equipment[]>(`${orgBase(organizationId)}/equipment`, { signal })
}
export function createEquipment(organizationId: string, body: EquipmentCreate): Promise<Equipment> {
  return apiRequest<Equipment>(`${orgBase(organizationId)}/equipment`, { method: 'POST', body })
}
export function updateEquipment(organizationId: string, id: string, body: EquipmentUpdate): Promise<Equipment> {
  return apiRequest<Equipment>(`${orgBase(organizationId)}/equipment/${seg(id)}`, { method: 'PATCH', body })
}
export function deleteEquipment(organizationId: string, id: string): Promise<void> {
  return apiRequest<void>(`${orgBase(organizationId)}/equipment/${seg(id)}`, { method: 'DELETE' })
}

// ---- Chemicals ----
export function listChemicals(organizationId: string, signal?: AbortSignal): Promise<Chemical[]> {
  return apiRequest<Chemical[]>(`${orgBase(organizationId)}/chemicals`, { signal })
}
export function createChemical(organizationId: string, body: ChemicalCreate): Promise<Chemical> {
  return apiRequest<Chemical>(`${orgBase(organizationId)}/chemicals`, { method: 'POST', body })
}
export function updateChemical(organizationId: string, id: string, body: ChemicalUpdate): Promise<Chemical> {
  return apiRequest<Chemical>(`${orgBase(organizationId)}/chemicals/${seg(id)}`, { method: 'PATCH', body })
}
export function deleteChemical(organizationId: string, id: string): Promise<void> {
  return apiRequest<void>(`${orgBase(organizationId)}/chemicals/${seg(id)}`, { method: 'DELETE' })
}

// ---- Medical checks ----
export function listMedicalChecks(organizationId: string, signal?: AbortSignal): Promise<MedicalCheck[]> {
  return apiRequest<MedicalCheck[]>(`${orgBase(organizationId)}/medical-checks`, { signal })
}
export function createMedicalCheck(organizationId: string, body: MedicalCheckCreate): Promise<MedicalCheck> {
  return apiRequest<MedicalCheck>(`${orgBase(organizationId)}/medical-checks`, { method: 'POST', body })
}
export function updateMedicalCheck(organizationId: string, id: string, body: MedicalCheckUpdate): Promise<MedicalCheck> {
  return apiRequest<MedicalCheck>(`${orgBase(organizationId)}/medical-checks/${seg(id)}`, { method: 'PATCH', body })
}
export function deleteMedicalCheck(organizationId: string, id: string): Promise<void> {
  return apiRequest<void>(`${orgBase(organizationId)}/medical-checks/${seg(id)}`, { method: 'DELETE' })
}

// ---- Attachments (equipment manuals, chemical safety data sheets) ----
export type DocumentOwner = 'equipment' | 'chemicals'

export function uploadAttachment(organizationId: string, file: File): Promise<Attachment> {
  const form = new FormData()
  form.append('file', file)
  return apiRequest<Attachment>(`${orgBase(organizationId)}/attachments`, { method: 'POST', body: form })
}

/** Uploads the file, then links it to the equipment / chemical. Returns the updated owner. */
export async function attachDocument<T extends Equipment | Chemical>(
  organizationId: string,
  owner: DocumentOwner,
  ownerId: string,
  file: File,
): Promise<T> {
  const attachment = await uploadAttachment(organizationId, file)
  return apiRequest<T>(`${orgBase(organizationId)}/${owner}/${seg(ownerId)}/attachment`, {
    method: 'POST',
    body: { attachment_id: attachment.id },
  })
}

/** Unlinks and deletes the stored file. */
export function detachDocument<T extends Equipment | Chemical>(
  organizationId: string,
  owner: DocumentOwner,
  ownerId: string,
): Promise<T> {
  return apiRequest<T>(`${orgBase(organizationId)}/${owner}/${seg(ownerId)}/attachment`, { method: 'DELETE' })
}

export function downloadAttachment(organizationId: string, attachmentId: string): Promise<DownloadedFile> {
  return apiDownload(`${orgBase(organizationId)}/attachments/${seg(attachmentId)}`)
}
