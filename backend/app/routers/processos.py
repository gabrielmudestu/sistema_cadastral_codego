from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import ProcessoDocumento, StatusProcesso
from app.schemas.cadastro import ProcessoOut

router = APIRouter()


@router.get("", response_model=list[ProcessoOut])
def listar_processos(
    status: StatusProcesso | None = Query(default=None, description="Filtrar por status"),
    db: Session = Depends(get_db),
):
    """Lista os processos cadastrais, opcionalmente filtrados por status."""
    query = db.query(ProcessoDocumento)
    if status is not None:
        query = query.filter(ProcessoDocumento.status == status)
    return query.order_by(ProcessoDocumento.data_geracao.desc()).all()


@router.get("/protocolo/{protocolo}", response_model=ProcessoOut)
def consultar_por_protocolo(protocolo: str, db: Session = Depends(get_db)):
    """Consulta um processo pelo número de protocolo (ex: REC-2026-89421)."""
    processo = (
        db.query(ProcessoDocumento)
        .filter(ProcessoDocumento.protocolo == protocolo)
        .first()
    )
    if processo is None:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado.")
    return processo
