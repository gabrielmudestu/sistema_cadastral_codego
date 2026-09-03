from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str
    email: str
    telefone: str | None
    cargo: str | None
    data_criacao: datetime


class ProcessoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    protocolo: str
    tipo_documento: str
    status: str
    caminho_pdf_preenchido: str | None
    caminho_pdf_assinado: str | None
    data_geracao: datetime
    data_upload_assinado: datetime | None


class CadastroResponse(BaseModel):
    usuario: UsuarioOut
    processo: ProcessoOut
    pdf_download_url: str
