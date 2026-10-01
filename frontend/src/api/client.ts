import type { Case, Evidence, Investigation } from '../types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  listCases: () => request<Case[]>('/cases'),
  createCase: (data: { name: string; business_name?: string }) =>
    request<Case>('/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
  getCase: (id: string) => request<Case>(`/cases/${id}`),

  listEvidenceCategories: (caseId: string) =>
    request<string[]>(`/cases/${caseId}/evidence/categories`),
  listEvidence: (caseId: string) => request<Evidence[]>(`/cases/${caseId}/evidence`),
  uploadEvidence: (caseId: string, file: File, category: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('category', category)
    return request<Evidence>(`/cases/${caseId}/evidence`, { method: 'POST', body: form })
  },
  deleteEvidence: (caseId: string, evidenceId: string) =>
    request<{ ok: boolean }>(`/cases/${caseId}/evidence/${evidenceId}`, { method: 'DELETE' }),

  runInvestigation: (caseId: string) =>
    request<Investigation>(`/cases/${caseId}/investigate`, { method: 'POST' }),
  listInvestigations: (caseId: string) =>
    request<Investigation[]>(`/cases/${caseId}/investigations`),
}
