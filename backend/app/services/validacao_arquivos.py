import os

from fastapi import UploadFile, HTTPException

from app.config import settings

EXTENSOES_DOCUMENTO_ASSINADO = {".pdf"}
EXTENSOES_ANEXO_PERMITIDAS = {".pdf", ".png", ".jpg", ".jpeg"}
MIME_PERMITIDOS = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}


def _validar_tamanho(tamanho_bytes: int):
    limite = settings.max_upload_size_mb * 1024 * 1024
    if tamanho_bytes > limite:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {settings.max_upload_size_mb}MB.",
        )


def validar_documento_assinado(file: UploadFile, conteudo: bytes):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in EXTENSOES_DOCUMENTO_ASSINADO:
        raise HTTPException(status_code=422, detail="O documento assinado deve ser um arquivo PDF.")
    if file.content_type not in MIME_PERMITIDOS:
        raise HTTPException(status_code=422, detail="Tipo de arquivo não permitido.")
    _validar_tamanho(len(conteudo))


def validar_anexo(file: UploadFile, conteudo: bytes):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in EXTENSOES_ANEXO_PERMITIDAS:
        raise HTTPException(
            status_code=422,
            detail="Anexo deve ser PDF, PNG ou JPG.",
        )
    if file.content_type not in MIME_PERMITIDOS:
        raise HTTPException(status_code=422, detail="Tipo de arquivo não permitido.")
    _validar_tamanho(len(conteudo))


def salvar_arquivo(conteudo: bytes, diretorio: str, nome_arquivo: str) -> str:
    os.makedirs(diretorio, exist_ok=True)
    caminho = os.path.join(diretorio, nome_arquivo)
    with open(caminho, "wb") as f:
        f.write(conteudo)
    return caminho
