import random
from datetime import datetime

from app.config import settings


def gerar_protocolo() -> str:
    """Gera um protocolo no formato PREFIX-ANO-NNNNN, ex: REC-2026-89421."""
    ano = datetime.now().year
    sufixo = random.randint(10000, 99999)
    return f"{settings.protocol_prefix}-{ano}-{sufixo}"


def mascarar_documento(documento: str) -> str:
    """Mascara CPF/CNPJ mantendo só os 3 primeiros dígitos visíveis, como no protótipo."""
    digits = "".join(filter(str.isdigit, documento))
    if len(digits) == 11:  # CPF
        return f"{digits[:3]}.***.***-**"
    if len(digits) == 14:  # CNPJ
        return f"{digits[:2]}.***.***/****-**"
    return "***"
