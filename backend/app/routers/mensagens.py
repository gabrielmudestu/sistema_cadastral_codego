import json

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.orm import Mensagem, AnexoMensagem
from app.schemas.mensagens import MensagemOut
from app.services.validacao_arquivos import validar_anexo, salvar_arquivo

router = APIRouter()


@router.post("", response_model=MensagemOut, status_code=201)
async def enviar_mensagem(
    remetente_nome: str = Form(...),
    assunto: str = Form(...),
    conteudo: str = Form(...),
    processo_id: int | None = Form(None),
    anexos: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    """Módulo de Mensagem e Anexos: envia uma mensagem com anexos complementares (Etapa 4)."""
    mensagem = Mensagem(
        processo_id=processo_id,
        remetente_nome=remetente_nome,
        assunto=assunto,
        conteudo=conteudo,
    )
    db.add(mensagem)
    db.commit()
    db.refresh(mensagem)

    for anexo in anexos:
        conteudo_bytes = await anexo.read()
        if not conteudo_bytes:
            continue
        validar_anexo(anexo, conteudo_bytes)
        nome_storage = f"msg{mensagem.id}_{anexo.filename}"
        caminho = salvar_arquivo(conteudo_bytes, settings.upload_dir, nome_storage)

        registro_anexo = AnexoMensagem(
            mensagem_id=mensagem.id,
            nome_original=anexo.filename,
            caminho_storage=caminho,
            tamanho_bytes=len(conteudo_bytes),
            tipo_mime=anexo.content_type or "application/octet-stream",
        )
        db.add(registro_anexo)

    db.commit()
    db.refresh(mensagem)

    return mensagem


@router.get("/{processo_id}", response_model=list[MensagemOut])
def listar_mensagens_do_processo(processo_id: int, db: Session = Depends(get_db)):
    """Lista as mensagens vinculadas a um processo específico."""
    return db.query(Mensagem).filter(Mensagem.processo_id == processo_id).all()
