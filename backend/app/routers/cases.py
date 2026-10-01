from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..db import get_session
from ..models.case import CaseCreate, CaseRead
from ..services import case_service

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("", response_model=CaseRead)
def create_case(data: CaseCreate, session: Session = Depends(get_session)) -> CaseRead:
    case = case_service.create_case(session, data)
    return CaseRead.model_validate(case)


@router.get("", response_model=list[CaseRead])
def list_cases(session: Session = Depends(get_session)) -> list[CaseRead]:
    cases = case_service.list_cases(session)
    return [CaseRead.model_validate(c) for c in cases]


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: str, session: Session = Depends(get_session)) -> CaseRead:
    case = case_service.get_case(session, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseRead.model_validate(case)
