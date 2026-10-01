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

export interface ToolCallRecord {
  step: number
  thought: string
  tool: string
  tool_input: Record<string, unknown>
  tool_output: Record<string, unknown>
  output_summary: string
}

export interface InvoiceReconciliation {
  invoice_id: string
  date: string
  amount: number
  paid: number
  balance: number
  status: 'paid' | 'partial' | 'unpaid' | 'overpaid'
  age_days: number
  eligible: boolean
  ineligibility_reason: string | null
}

export interface DuplicateInvoice {
  invoice_id: string
  amount: number
  occurrences: number
  excluded_amount: number
}

export interface UnallocatedReceipt {
  receipt_id: string
  amount: number
  reason: string
}

export interface DebtorReconciliation {
  invoices: InvoiceReconciliation[]
  total_outstanding: number
  total_eligible_outstanding: number
  duplicate_invoices: DuplicateInvoice[]
  unallocated_receipts: UnallocatedReceipt[]
  warnings: string[]
}

export interface VarianceFlag {
  field: string
  from_period: string
  to_period: string
  from_value: number
  to_value: number
  pct_change: number
  message: string
}

export interface ConsistencyResult {
  flags: VarianceFlag[]
}

export interface InvestigationDetails {
  tool_trace: ToolCallRecord[]
  debtor_reconciliation: DebtorReconciliation | null
  consistency: ConsistencyResult | null
  reconciliation: ReconciliationResult | null
  findings: Finding[]
  stopped_reason: string
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
