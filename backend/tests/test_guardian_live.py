"""
Live integration test: exercises the real pipeline (extraction LLM call ->
deterministic reconciliation -> findings LLM call) against the actual
configured Gemini key. Skipped automatically when no key is present (e.g.
CI, or a clone without .env) so the rest of the suite stays runnable without
network access or quota.
"""

import os

import pytest
from sqlmodel import Session

from app.agent.guardian import WorkingCapitalGuardian
from app.db import engine, init_db
from app.services import case_service, evidence_service
from app.models.case import CaseCreate

pytestmark = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"), reason="No GOOGLE_API_KEY configured -- skipping live LLM test"
)


FACILITY_AND_RECORDS_TEXT = """
Combined Facility & Records Note -- Test Fixture Pvt Ltd

Bank sanction terms: Cash Credit limit sanctioned at Rs. 10,00,000. Margin of 20% on stock,
margin of 50% on eligible book debts. Only debts under 90 days are eligible.

Current stock-in-trade value as per latest stock statement: Rs. 4,00,000.
Eligible book debts (under 90 days): Rs. 2,00,000.
Sundry creditors outstanding: Rs. 50,000.
"""

BANK_STATEMENT_TEXT = """
Cash Credit Account Statement
Drawing Power recognised: Rs. 3,00,000
Outstanding balance: Rs. 2,80,000
"""


def test_full_pipeline_against_live_gemini(tmp_path):
    init_db()
    with Session(engine) as session:
        case = case_service.create_case(session, CaseCreate(name="Live pipeline test case"))

        ev1 = evidence_service.add_evidence(
            session,
            case_id=case.id,
            original_filename="facility_and_records.txt",
            content_type="text/plain",
            content=FACILITY_AND_RECORDS_TEXT.encode(),
            category="other",
        )
        ev2 = evidence_service.add_evidence(
            session,
            case_id=case.id,
            original_filename="bank_statement.txt",
            content_type="text/plain",
            content=BANK_STATEMENT_TEXT.encode(),
            category="bank_statement",
        )

        result = WorkingCapitalGuardian().investigate(case.name, [ev1, ev2])

    assert result.status == "complete"
    assert result.outcome is not None
    reconciliation = result.outcome.reconciliation
    assert reconciliation.can_calculate is True, (
        f"Expected a calculable reconciliation; missing_inputs={reconciliation.missing_inputs}"
    )
    # 400,000*0.8 + 200,000*0.5 - 50,000 = 370,000 ; reported 300,000 -> gap 70,000
    assert reconciliation.calculated_dp == 370_000.0
    assert reconciliation.gap == 70_000.0

    headline = result.outcome.findings[0]
    assert headline.status == "supported"
    assert headline.amount_impact == 70_000.0
