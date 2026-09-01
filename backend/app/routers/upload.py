import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.orm import ProcessoDocumento, StatusProcesso
from app.services.validacao_arquivos import validar_documento_assinado, salvar_arquivo

router = APIRouter()


@router.get("/{processo_id}/pdf")
def baixar_pdf_preenchido(processo_id: int, db: Session = Depends(get_db)):
    """Disponibiliza o PDF preenchido gerado na Etapa 1 para download."""
    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None or not processo.caminho_pdf_preenchido:
        raise HTTPException(status_code=404, detail="PDF não encontrado para este processo.")
    if not os.path.exists(processo.caminho_pdf_preenchido):
        raise HTTPException(status_code=404, detail="Arquivo do PDF não está mais disponível no servidor.")

    return FileResponse(
        processo.caminho_pdf_preenchido,
        media_type="application/pdf",
        filename=f"{processo.protocolo}_cadastro.pdf",
    )


@router.post("/{processo_id}/assinado")
async def enviar_documento_assinado(
    processo_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Recebe o reenvio do documento assinado (Etapa 2 do fluxo)."""
    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")

    conteudo = await arquivo.read()
    validar_documento_assinado(arquivo, conteudo)

    nome_arquivo = f"{processo.protocolo}_assinado.pdf"
    caminho = salvar_arquivo(conteudo, settings.signed_dir, nome_arquivo)

    processo.caminho_pdf_assinado = caminho
    processo.status = StatusProcesso.ASSINADO
    processo.data_upload_assinado = datetime.now()
    db.commit()
    db.refresh(processo)

    return {
        "mensagem": "Documento assinado recebido com sucesso.",
        "processo_id": processo.id,
        "status": processo.status,
    }
