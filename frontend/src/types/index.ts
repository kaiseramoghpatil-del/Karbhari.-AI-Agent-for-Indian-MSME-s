export interface Case {
  id: string
  name: string
  business_name: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface Evidence {
  id: string
  case_id: string
  original_filename: string
  content_type: string | null
  size_bytes: number
  category: string
  status: string
  uploaded_at: string
}

export type FindingStatus = 'supported' | 'unresolved' | 'ineligible_contradicted'

export interface Finding {
  title: string
  status: FindingStatus
  explanation: string
  amount_impact: number | null
  evidence_ids: string[]
  evidence_quotes: string[]
}

export interface ReconciliationResult {
  calculated_dp: number | null
  comparison_basis: 'reported_drawing_power' | 'current_outstanding' | 'none'
  comparison_value: number | null
  gap: number | null
  assumptions_used: string[]
  missing_inputs: string[]
  can_calculate: boolean
}

export interface EvidenceExtraction {
  evidence_id: string
  original_filename: string
  category: string
  facts: Record<string, unknown>
}

export interface InvestigationDetails {
  extractions: EvidenceExtraction[]
  aggregated_facts: Record<string, unknown> | null
  reconciliation: ReconciliationResult | null
  findings: Finding[]
}

export interface Investigation {
  id: string
  case_id: string
  status: string
  summary: string
  evidence_count_considered: number
  details: InvestigationDetails | null
  started_at: string
  completed_at: string | null
}
