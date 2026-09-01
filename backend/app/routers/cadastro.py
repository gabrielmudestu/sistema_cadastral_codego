from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Usuario, ProcessoDocumento, StatusProcesso
from app.schemas.cadastro import CadastroCreate, CadastroResponse
from app.services.protocolo import gerar_protocolo
from app.services.pdf_generator import gerar_pdf_anexo_viii_d

router = APIRouter()


@router.post("", response_model=CadastroResponse, status_code=201)
def criar_cadastro(payload: CadastroCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário, abre um novo processo com protocolo único
    e gera o PDF preenchido para download (Etapa 1 do fluxo).
    """
    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.documento).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome,
            cpf_cnpj=payload.documento,
            email=payload.email,
            telefone=payload.telefone,
            cargo=payload.cargo,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_viii_d(usuario, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
    )


@router.get("/{processo_id}")
def obter_cadastro(processo_id: int, db: Session = Depends(get_db)):
    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    return processo
