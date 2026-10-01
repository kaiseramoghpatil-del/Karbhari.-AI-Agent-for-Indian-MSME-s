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

export interface Investigation {
  id: string
  case_id: string
  status: string
  summary: string
  evidence_count_considered: number
  started_at: string
  completed_at: string | null
}
