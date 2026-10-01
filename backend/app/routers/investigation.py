from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..db import get_session
from ..models.investigation import Investigation, InvestigationRead
from ..services import case_service, investigation_service

router = APIRouter(prefix="/api/cases/{case_id}", tags=["investigation"])


def _to_read(investigation: Investigation) -> InvestigationRead:
    return InvestigationRead(
        id=investigation.id,
        case_id=investigation.case_id,
        status=investigation.status,
        summary=investigation.summary,
        evidence_count_considered=investigation.evidence_count_considered,
        details=investigation_service.investigation_details(investigation),
        started_at=investigation.started_at,
        completed_at=investigation.completed_at,
    )


@router.post("/investigate", response_model=InvestigationRead)
def investigate(case_id: str, session: Session = Depends(get_session)) -> InvestigationRead:
    case = case_service.get_case(session, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    investigation = investigation_service.run_investigation(session, case)
    return _to_read(investigation)


@router.get("/investigations", response_model=list[InvestigationRead])
def list_investigations(
    case_id: str, session: Session = Depends(get_session)
) -> list[InvestigationRead]:
    case = case_service.get_case(session, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    items = investigation_service.list_investigations(session, case_id)
    return [_to_read(i) for i in items]
