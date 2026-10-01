"""
Domain types for deterministic reconciliation -- separate from agent/schemas.py
(which describes LLM input/output contracts). These describe real accounting
records and the results of reconciling them.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

InvoiceStatus = Literal["paid", "partial", "unpaid", "overpaid"]


class Invoice(BaseModel):
    invoice_id: str
    date: date
    amount: float
    debtor_name: str | None = None
    source_evidence_id: str | None = None


class Receipt(BaseModel):
    receipt_id: str
    date: date
    amount: float
    # None means the receipt is tagged to the debtor but not to a specific
    # invoice -- the realistic case for most Tally-style ledgers, which is
    # exactly why FIFO allocation (not a simple join) is needed.
    matched_invoice_id: str | None = None
    debtor_name: str | None = None
    source_evidence_id: str | None = None


class InvoiceReconciliation(BaseModel):
    invoice_id: str
    date: date
    amount: float
    paid: float
    balance: float
    status: InvoiceStatus
    age_days: int
    eligible: bool
    ineligibility_reason: str | None = None


class DuplicateInvoice(BaseModel):
    invoice_id: str
    amount: float
    occurrences: int
    excluded_amount: float  # the amount excluded from totals because of the duplicate


class UnallocatedReceipt(BaseModel):
    receipt_id: str
    amount: float
    reason: str


class DebtorReconciliationResult(BaseModel):
    invoices: list[InvoiceReconciliation] = Field(default_factory=list)
    total_outstanding: float = 0.0
    total_eligible_outstanding: float = 0.0
    duplicate_invoices: list[DuplicateInvoice] = Field(default_factory=list)
    unallocated_receipts: list[UnallocatedReceipt] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PeriodFigure(BaseModel):
    period_label: str
    value: float
    source_evidence_id: str | None = None


class VarianceFlag(BaseModel):
    field: str
    from_period: str
    to_period: str
    from_value: float
    to_value: float
    pct_change: float
    message: str


class ConsistencyResult(BaseModel):
    flags: list[VarianceFlag] = Field(default_factory=list)
