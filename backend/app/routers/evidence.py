from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from ..db import get_session
from ..models.evidence import EVIDENCE_CATEGORIES, EvidenceRead
from ..services import case_service, evidence_service

router = APIRouter(prefix="/api/cases/{case_id}/evidence", tags=["evidence"])


def _require_case(session: Session, case_id: str):
    case = case_service.get_case(session, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/categories")
def list_categories() -> list[str]:
    return EVIDENCE_CATEGORIES


@router.post("", response_model=EvidenceRead)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    category: str = Form("other"),
    session: Session = Depends(get_session),
) -> EvidenceRead:
    _require_case(session, case_id)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    evidence = evidence_service.add_evidence(
        session,
        case_id=case_id,
        original_filename=file.filename or "unnamed",
        content_type=file.content_type,
        content=content,
        category=category if category in EVIDENCE_CATEGORIES else "other",
    )
    return EvidenceRead.model_validate(evidence)


@router.get("", response_model=list[EvidenceRead])
def list_evidence(case_id: str, session: Session = Depends(get_session)) -> list[EvidenceRead]:
    _require_case(session, case_id)
    items = evidence_service.list_evidence(session, case_id)
    return [EvidenceRead.model_validate(e) for e in items]


@router.delete("/{evidence_id}")
def delete_evidence(
    case_id: str, evidence_id: str, session: Session = Depends(get_session)
) -> dict:
    _require_case(session, case_id)
    deleted = evidence_service.delete_evidence(session, evidence_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return {"ok": True}
