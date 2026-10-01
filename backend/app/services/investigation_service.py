from __future__ import annotations

from sqlmodel import Session, select

from ..agent.guardian import WorkingCapitalGuardian
from ..models.case import Case
from ..models.investigation import Investigation
from . import evidence_service


def run_investigation(session: Session, case: Case) -> Investigation:
    evidence = evidence_service.list_evidence(session, case.id)
    result = WorkingCapitalGuardian().investigate(case.name, evidence)

    investigation = Investigation(
        case_id=case.id,
        status=result.status,
        summary=result.summary,
        evidence_count_considered=result.evidence_count_considered,
    )
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    return investigation


def list_investigations(session: Session, case_id: str) -> list[Investigation]:
    return list(
        session.exec(
            select(Investigation)
            .where(Investigation.case_id == case_id)
            .order_by(Investigation.started_at.desc())
        )
    )
