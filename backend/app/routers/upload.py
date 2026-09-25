import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.orm import DocumentoProcesso, ProcessoDocumento, StatusProcesso
from app.services.documentos_processo import documentos_exigidos
from app.services.validacao_arquivos import validar_anexo, validar_documento_assinado, salvar_arquivo
from app.services.email_service import enviar_email_documento_assinado
from app.services.recaptcha import verificar_recaptcha

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


@router.get("/{processo_id}/documentos-exigidos")
def listar_documentos_exigidos(processo_id: int, db: Session = Depends(get_db)):
    """
    Documentos que devem acompanhar o documento assinado (os que a pessoa
    marcou no formulário). Lista vazia quando o anexo não exige documentos.
    """
    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    return documentos_exigidos(processo)


async def _ler_documentos(
    documentos: list[UploadFile],
    documentos_codigos: list[str],
    exigidos: list[dict[str, str]],
) -> list[tuple[dict[str, str], UploadFile, bytes]]:
    """
    Confere se veio exatamente um arquivo para cada documento exigido e valida
    cada um (tipo e tamanho). Tudo é conferido antes de salvar qualquer coisa.
    """
    if len(documentos) != len(documentos_codigos):
        raise HTTPException(status_code=422, detail="Envio de documentos inconsistente. Tente novamente.")

    exigidos_por_codigo = {doc["codigo"]: doc for doc in exigidos}
    recebidos: dict[str, tuple[UploadFile, bytes]] = {}
    for arquivo_doc, codigo in zip(documentos, documentos_codigos):
        if codigo not in exigidos_por_codigo or codigo in recebidos:
            raise HTTPException(status_code=422, detail="Documento anexado não corresponde ao requerimento.")
        conteudo_doc = await arquivo_doc.read()
        if not conteudo_doc:
            continue
        try:
            validar_anexo(arquivo_doc, conteudo_doc)
        except HTTPException as erro:
            raise HTTPException(
                status_code=erro.status_code,
                detail=f"{exigidos_por_codigo[codigo]['descricao'].rstrip(';')} — {erro.detail}",
            )
        recebidos[codigo] = (arquivo_doc, conteudo_doc)

    faltando = [doc["descricao"] for doc in exigidos if doc["codigo"] not in recebidos]
    if faltando:
        raise HTTPException(status_code=422, detail=f"Anexe o documento: {faltando[0]}")

    return [(doc, *recebidos[doc["codigo"]]) for doc in exigidos]


@router.post("/{processo_id}/assinado")
async def enviar_documento_assinado(
    processo_id: int,
    arquivo: UploadFile = File(...),
    documentos: list[UploadFile] = File(default=[]),
    documentos_codigos: list[str] = Form(default=[]),
    g_recaptcha_response: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """
    Recebe o reenvio do documento assinado (Etapa 2 do fluxo), junto com os
    documentos que acompanham o requerimento (ex.: os marcados no Anexo III).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")

    conteudo = await arquivo.read()
    validar_documento_assinado(arquivo, conteudo)
    documentos_lidos = await _ler_documentos(documentos, documentos_codigos, documentos_exigidos(processo))

    nome_arquivo = f"{processo.protocolo}_assinado.pdf"
    caminho = salvar_arquivo(conteudo, settings.signed_dir, nome_arquivo)

    # Um novo envio substitui os documentos enviados antes para este protocolo.
    for anterior in list(processo.documentos):
        if os.path.exists(anterior.caminho_storage):
            os.remove(anterior.caminho_storage)
        processo.documentos.remove(anterior)

    diretorio_documentos = os.path.join(settings.upload_dir, "documentos", processo.protocolo)
    for doc, arquivo_doc, conteudo_doc in documentos_lidos:
        extensao = os.path.splitext(arquivo_doc.filename or "")[1].lower()
        processo.documentos.append(
            DocumentoProcesso(
                codigo=doc["codigo"],
                descricao=doc["descricao"],
                nome_original=arquivo_doc.filename,
                caminho_storage=salvar_arquivo(conteudo_doc, diretorio_documentos, f"{doc['codigo']}{extensao}"),
                tamanho_bytes=len(conteudo_doc),
                tipo_mime=arquivo_doc.content_type or "application/octet-stream",
            )
        )

    processo.caminho_pdf_assinado = caminho
    processo.status = StatusProcesso.ASSINADO
    processo.data_upload_assinado = datetime.now()
    db.commit()
    db.refresh(processo)

    documentos_recebidos = [doc.descricao for doc in processo.documentos]

    dados_formulario = processo.dados_formulario or {}
    nome_empresarial = (
        dados_formulario.get("nome_empresarial")
        or dados_formulario.get("nome_empresa")
        or dados_formulario.get("razao_social")
        or (processo.usuario.nome if processo.usuario else "")
    )

    # Todos os documentos assinados são enviados para o e-mail fixo da empresa
    # (NOTIFICATION_EMAIL), não para o e-mail que a pessoa preencheu no cadastro.
    # Se NOTIFICATION_EMAIL não estiver configurado, cai para o e-mail do cadastro
    # (quando houver — o CFO, por exemplo, não pede e-mail).
    destinatario = settings.notification_email or (processo.usuario.email if processo.usuario else "")

    if destinatario:
        email_enviado, email_erro = enviar_email_documento_assinado(
            destinatario_email=destinatario,
            nome_empresarial=nome_empresarial,
            protocolo=processo.protocolo,
            caminho_pdf_assinado=caminho,
            documentos_recebidos=documentos_recebidos,
        )
    else:
        email_enviado, email_erro = False, "Nenhum e-mail de destino configurado (NOTIFICATION_EMAIL)."

    return {
        "mensagem": "Documento assinado recebido com sucesso.",
        "processo_id": processo.id,
        "status": processo.status,
        "documentos_recebidos": documentos_recebidos,
        "email_enviado": email_enviado,
        "email_destinatario": destinatario,
        "email_erro": email_erro,
    }
