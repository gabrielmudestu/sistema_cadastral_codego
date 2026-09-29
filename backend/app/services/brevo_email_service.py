import base64
import logging
import os

import requests

from app.config import settings

logger = logging.getLogger("codego.email")

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

AVISO_ANEXOS_RECUSADOS_TEXTO = (
    "\n\nObservação: os arquivos não puderam ser anexados a este e-mail "
    "(limite de tamanho do serviço de e-mail)."
)
AVISO_ANEXOS_RECUSADOS_HTML = (
    "<p><em>Observação: os arquivos não puderam ser anexados a este e-mail "
    "(limite de tamanho do serviço de e-mail).</em></p>"
)


def enviar_via_brevo(
    destinatario_email: str,
    assunto: str,
    corpo_html: str,
    corpo_texto: str,
    anexos: list[tuple[str, str]] | None = None,
) -> tuple[bool, str | None]:
    """
    Envia um e-mail pela API web do Brevo (https, porta 443) — usado quando
    EMAIL_PROVIDER=brevo_api, ex.: no Render grátis, que bloqueia as portas de
    SMTP. `anexos` é uma lista de (caminho do arquivo, nome no e-mail).
    Se o Brevo recusar o e-mail com anexos (ex.: tamanho), tenta de novo sem
    eles, avisando no corpo. Retorna (True, None) em sucesso ou (False, motivo)
    — nunca levanta exceção.
    """
    if not settings.brevo_api_key:
        motivo = "BREVO_API_KEY não configurada."
        logger.warning(motivo)
        return False, motivo

    remetente = settings.brevo_sender_email or settings.smtp_from_email
    if not remetente:
        motivo = "BREVO_SENDER_EMAIL não configurado."
        logger.warning(motivo)
        return False, motivo

    lista_anexos = []
    for caminho, nome_arquivo in anexos or []:
        try:
            with open(caminho, "rb") as f:
                lista_anexos.append({"name": nome_arquivo, "content": base64.b64encode(f.read()).decode("ascii")})
        except OSError as erro:
            logger.warning("Não foi possível ler %s para anexar: %s", os.path.basename(caminho), erro)

    corpo = {
        "sender": {"email": remetente, "name": settings.smtp_from_name},
        "to": [{"email": destinatario_email}],
        "subject": assunto,
        "htmlContent": corpo_html,
        "textContent": corpo_texto,
    }
    if lista_anexos:
        corpo["attachment"] = lista_anexos

    ok, motivo, status = _postar(corpo)
    if not ok and lista_anexos and status is not None and 400 <= status < 500 and status not in (401, 403):
        logger.warning("Brevo recusou o e-mail com anexos (%s); reenviando sem anexos.", motivo)
        corpo.pop("attachment")
        corpo["htmlContent"] = corpo_html + AVISO_ANEXOS_RECUSADOS_HTML
        corpo["textContent"] = corpo_texto + AVISO_ANEXOS_RECUSADOS_TEXTO
        ok, motivo, status = _postar(corpo)

    if ok:
        logger.info("E-mail (Brevo API) enviado para %s: %s", destinatario_email, assunto)
    return ok, motivo


def _postar(corpo: dict) -> tuple[bool, str | None, int | None]:
    try:
        resposta = requests.post(
            BREVO_SEND_URL,
            headers={"api-key": settings.brevo_api_key, "accept": "application/json"},
            json=corpo,
            timeout=30,
        )
    except requests.RequestException as erro:
        logger.exception("Falha de rede ao enviar e-mail pelo Brevo")
        return False, f"{type(erro).__name__}: {erro}", None

    if resposta.status_code in (200, 201, 202):
        return True, None, resposta.status_code

    motivo = f"HTTP {resposta.status_code}: {resposta.text[:300]}"
    logger.warning("Falha ao enviar e-mail pelo Brevo: %s", motivo)
    return False, motivo, resposta.status_code
