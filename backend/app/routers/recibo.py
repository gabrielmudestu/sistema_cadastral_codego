from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import ProcessoDocumento, StatusProcesso
from app.schemas.mensagens import ReciboOut
from app.services.protocolo import mascarar_documento

router = APIRouter()

DECLARACAO_PADRAO = (
    "Confirmamos o recebimento com sucesso do documento cadastral assinado enviado pelo "
    "usuário. Este recibo comprova a entrega dos arquivos para os devidos fins de validação "
    "e processamento interno."
)


@router.get("/{processo_id}", response_model=ReciboOut)
def obter_recibo(processo_id: int, db: Session = Depends(get_db)):
    """
    Gera/retorna o recibo eletrônico de um processo já assinado (Etapa 3 do fluxo),
    com protocolo, data/hora e declaração de recebimento.
    """
    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")

    if processo.status != StatusProcesso.ASSINADO:
        raise HTTPException(
            status_code=409,
            detail="Recibo só pode ser emitido após o upload do documento assinado.",
        )

    if not processo.texto_recibo:
        processo.texto_recibo = DECLARACAO_PADRAO
        db.commit()
        db.refresh(processo)

    arquivos = [f for f in [processo.caminho_pdf_assinado] if f]

    return ReciboOut(
        protocolo=processo.protocolo,
        data_hora=processo.data_upload_assinado,
        remetente_nome=processo.usuario.nome,
        remetente_documento_mascarado=mascarar_documento(processo.usuario.cpf_cnpj),
        declaracao=processo.texto_recibo,
        arquivos=arquivos,
    )
