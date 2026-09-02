import enum

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class StatusProcesso(str, enum.Enum):
    PENDENTE = "Pendente"
    ASSINADO = "Assinado"
    CANCELADO = "Cancelado"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cpf_cnpj = Column(String(20), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False)
    telefone = Column(String(30))
    cargo = Column(String(100))
    data_criacao = Column(DateTime, server_default=func.now())

    processos = relationship("ProcessoDocumento", back_populates="usuario")


class ProcessoDocumento(Base):
    __tablename__ = "processos_documentos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    protocolo = Column(String(50), nullable=False, unique=True, index=True)
    caminho_pdf_preenchido = Column(String(500))
    caminho_pdf_assinado = Column(String(500))
    status = Column(
        Enum(StatusProcesso, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
        default=StatusProcesso.PENDENTE,
    )
    texto_recibo = Column(Text)
    data_geracao = Column(DateTime, server_default=func.now())
    data_upload_assinado = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", back_populates="processos")
    mensagens = relationship("Mensagem", back_populates="processo")


class Mensagem(Base):
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, index=True)
    processo_id = Column(Integer, ForeignKey("processos_documentos.id"), nullable=True)
    remetente_nome = Column(String(255), nullable=False)
    assunto = Column(String(255), nullable=False)
    conteudo = Column(Text, nullable=False)
    data_envio = Column(DateTime, server_default=func.now())

    processo = relationship("ProcessoDocumento", back_populates="mensagens")
    anexos = relationship("AnexoMensagem", back_populates="mensagem")


class AnexoMensagem(Base):
    __tablename__ = "anexos_mensagem"

    id = Column(Integer, primary_key=True, index=True)
    mensagem_id = Column(Integer, ForeignKey("mensagens.id"), nullable=False)
    nome_original = Column(String(255), nullable=False)
    caminho_storage = Column(String(500), nullable=False)
    tamanho_bytes = Column(BigInteger, nullable=False)
    tipo_mime = Column(String(100), nullable=False)

    mensagem = relationship("Mensagem", back_populates="anexos")
