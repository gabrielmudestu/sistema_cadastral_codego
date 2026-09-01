from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReciboOut(BaseModel):
    protocolo: str
    data_hora: datetime
    remetente_nome: str
    remetente_documento_mascarado: str
    declaracao: str
    arquivos: list[str]


class MensagemCreate(BaseModel):
    processo_id: int | None = None
    remetente_nome: str
    assunto: str
    conteudo: str


class AnexoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_original: str
    tamanho_bytes: int
    tipo_mime: str


class MensagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    processo_id: int | None
    remetente_nome: str
    assunto: str
    conteudo: str
    data_envio: datetime
    anexos: list[AnexoOut] = []
