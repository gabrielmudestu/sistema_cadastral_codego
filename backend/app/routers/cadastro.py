import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Usuario, ProcessoDocumento, StatusProcesso, TipoDocumento
from app.schemas.cadastro import CadastroResponse
from app.schemas.anexo_viii_d import AnexoViiiDCreate
from app.services.protocolo import gerar_protocolo
from app.services.pdf_generator import gerar_pdf_anexo_viii_d

router = APIRouter()


@router.post("/anexo-viii-d", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_viii_d(payload: AnexoViiiDCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VIII-D com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Etapa 1 do fluxo).
    """
    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_viii_d(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VIII_D,
        dados_formulario=json.loads(payload.model_dump_json()),
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
