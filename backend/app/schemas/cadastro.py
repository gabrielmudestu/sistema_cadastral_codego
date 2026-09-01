from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class CadastroCreate(BaseModel):
    nome: str
    tipo_documento: str  # "cpf" ou "cnpj"
    documento: str  # apenas dígitos
    email: EmailStr
    telefone: str
    cargo: str

    @field_validator("documento")
    @classmethod
    def valida_documento(cls, v: str, info):
        digits = "".join(filter(str.isdigit, v))
        tipo = info.data.get("tipo_documento")
        esperado = 11 if tipo == "cpf" else 14
        if len(digits) != esperado:
            raise ValueError(f"{tipo.upper() if tipo else 'documento'} deve ter {esperado} dígitos")
        return digits

    @field_validator("telefone")
    @classmethod
    def valida_telefone(cls, v: str):
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Telefone deve ter DDD + número (mínimo 10 dígitos)")
        return digits


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
    status: str
    caminho_pdf_preenchido: str | None
    caminho_pdf_assinado: str | None
    data_geracao: datetime
    data_upload_assinado: datetime | None


class CadastroResponse(BaseModel):
    usuario: UsuarioOut
    processo: ProcessoOut
    pdf_download_url: str
