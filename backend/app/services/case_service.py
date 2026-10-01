"""
Case service layer.

Deliberately plain functions over a SQLModel Session, with no FastAPI
imports anywhere in this module. Both the HTTP routers and the aiKart
sandbox entrypoint call into these same functions, which is how "the same
application/service layer" requirement is satisfied without two
implementations of case logic.
"""

from __future__ import annotations

from sqlmodel import Session, select

from ..models.case import Case, CaseCreate


def create_case(session: Session, data: CaseCreate) -> Case:
    case = Case(name=data.name, business_name=data.business_name)
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


def get_case(session: Session, case_id: str) -> Case | None:
    return session.get(Case, case_id)


def list_cases(session: Session) -> list[Case]:
    return list(session.exec(select(Case).order_by(Case.created_at.desc())))
