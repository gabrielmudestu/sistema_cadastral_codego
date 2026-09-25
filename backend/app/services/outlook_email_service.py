import base64
import logging

import requests

from app.services.outlook_auth import obter_access_token

logger = logging.getLogger("codego.email.outlook")

GRAPH_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/me/sendMail"


def _montar_corpo_html(nome_empresarial: str, protocolo: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; color: #1a1a1a; font-size: 14px; line-height: 1.6;">
      <p>Olá,</p>
      <p>
        Confirmamos o recebimento do documento assinado referente ao processo de
        <strong>{nome_empresarial}</strong>.
      </p>
      <p style="font-family: monospace; background: #f2f2f2; padding: 8px 12px; display: inline-block;">
        Protocolo: <strong>{protocolo}</strong>
      </p>
      <p>
        Este e-mail confirma que o arquivo foi recebido e validado pelo
        <strong>Sistema Cadastral CODEGO</strong>. Em breve o recibo eletrônico
        deste processo estará disponível.
      </p>
      <p>Atenciosamente,<br>Companhia de Desenvolvimento Econômico de Goiás</p>
    </div>
    """


def enviar_email_documento_assinado_outlook(
    destinatario_email: str,
    nome_empresarial: str,
    protocolo: str,
    caminho_pdf_assinado: str,
) -> tuple[bool, str | None]:
    """
    Envia o e-mail de confirmação via Microsoft Graph API (OAuth2), usando o
    token obtido a partir do login único feito com scripts/setup_outlook_auth.py.
    Retorna (True, None) em sucesso, ou (False, motivo) em caso de falha — nunca
    levanta exceção.
    """
    access_token, erro_token = obter_access_token()
    if access_token is None:
        logger.warning("Não foi possível obter token do Outlook: %s", erro_token)
        return False, erro_token

    try:
        with open(caminho_pdf_assinado, "rb") as f:
            anexo_base64 = base64.b64encode(f.read()).decode("ascii")
    except OSError as erro:
        logger.warning("Não foi possível ler o PDF assinado para anexar: %s", erro)
        anexo_base64 = None

    corpo = {
        "message": {
            "subject": f"Documento assinado recebido — Protocolo {protocolo}",
            "body": {
                "contentType": "HTML",
                "content": _montar_corpo_html(nome_empresarial, protocolo),
            },
            "toRecipients": [{"emailAddress": {"address": destinatario_email}}],
        },
        "saveToSentItems": True,
    }

    if anexo_base64:
        corpo["message"]["attachments"] = [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": f"{protocolo}_assinado.pdf",
                "contentType": "application/pdf",
                "contentBytes": anexo_base64,
            }
        ]

    try:
        resposta = requests.post(
            GRAPH_SEND_MAIL_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=corpo,
            timeout=20,
        )
        if resposta.status_code == 202:
            logger.info(
                "E-mail (Outlook/Graph) enviado para %s (protocolo %s).", destinatario_email, protocolo
            )
            return True, None

        motivo = f"HTTP {resposta.status_code}: {resposta.text[:300]}"
        logger.warning("Falha ao enviar e-mail via Graph: %s", motivo)
        return False, motivo
    except requests.RequestException as erro:
        logger.exception("Falha de rede ao enviar e-mail via Graph")
        return False, f"{type(erro).__name__}: {erro}"


def enviar_email_protocolo_outlook(
    destinatario_email: str,
    nome_empresarial: str,
    nome_documento: str,
    protocolo: str,
    caminho_pdf: str,
) -> tuple[bool, str | None]:
    """
    Envia o e-mail com o número de protocolo e o PDF gerado em anexo via
    Microsoft Graph API (OAuth2). Retorna (True, None) em sucesso, ou
    (False, motivo) em caso de falha — nunca levanta exceção.
    """
    from app.services.email_service import montar_corpo_protocolo_html

    access_token, erro_token = obter_access_token()
    if access_token is None:
        logger.warning("Não foi possível obter token do Outlook: %s", erro_token)
        return False, erro_token

    try:
        with open(caminho_pdf, "rb") as f:
            anexo_base64 = base64.b64encode(f.read()).decode("ascii")
    except OSError as erro:
        logger.warning("Não foi possível ler o PDF gerado para anexar: %s", erro)
        anexo_base64 = None

    corpo = {
        "message": {
            "subject": f"Seu protocolo {protocolo} — {nome_documento}",
            "body": {
                "contentType": "HTML",
                "content": montar_corpo_protocolo_html(nome_empresarial, nome_documento, protocolo),
            },
            "toRecipients": [{"emailAddress": {"address": destinatario_email}}],
        },
        "saveToSentItems": True,
    }

    if anexo_base64:
        corpo["message"]["attachments"] = [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": f"{protocolo}.pdf",
                "contentType": "application/pdf",
                "contentBytes": anexo_base64,
            }
        ]

    try:
        resposta = requests.post(
            GRAPH_SEND_MAIL_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=corpo,
            timeout=20,
        )
        if resposta.status_code == 202:
            logger.info(
                "E-mail de protocolo (Outlook/Graph) enviado para %s (protocolo %s).", destinatario_email, protocolo
            )
            return True, None

        motivo = f"HTTP {resposta.status_code}: {resposta.text[:300]}"
        logger.warning("Falha ao enviar e-mail de protocolo via Graph: %s", motivo)
        return False, motivo
    except requests.RequestException as erro:
        logger.exception("Falha de rede ao enviar e-mail de protocolo via Graph")
        return False, f"{type(erro).__name__}: {erro}"


def _montar_corpo_mensagem_html(remetente_nome: str, assunto: str, conteudo: str, protocolo: str | None) -> str:
    linha_protocolo = (
        f'<p style="font-family: monospace; background: #f2f2f2; padding: 8px 12px; '
        f'display: inline-block;">Protocolo: <strong>{protocolo}</strong></p>'
        if protocolo
        else "<p><em>Sem protocolo vinculado.</em></p>"
    )
    return f"""
    <div style="font-family: Arial, sans-serif; color: #1a1a1a; font-size: 14px; line-height: 1.6;">
      <p>Olá,</p>
      <p>Uma nova mensagem foi recebida no <strong>Sistema Cadastral CODEGO</strong>.</p>
      <p><strong>Remetente:</strong> {remetente_nome}</p>
      <p><strong>Assunto:</strong> {assunto}</p>
      {linha_protocolo}
      <p><strong>Mensagem:</strong><br>{conteudo}</p>
      <p>Atenciosamente,<br>Sistema Cadastral CODEGO</p>
    </div>
    """


def enviar_email_nova_mensagem_outlook(
    destinatario_email: str,
    remetente_nome: str,
    assunto: str,
    conteudo: str,
    protocolo: str | None,
    caminhos_anexos: list[str],
) -> tuple[bool, str | None]:
    """
    Envia o e-mail de notificação de nova mensagem via Microsoft Graph API
    (OAuth2). Retorna (True, None) em sucesso, ou (False, motivo) em caso de
    falha — nunca levanta exceção.
    """
    access_token, erro_token = obter_access_token()
    if access_token is None:
        logger.warning("Não foi possível obter token do Outlook: %s", erro_token)
        return False, erro_token

    anexos_graph = []
    for caminho in caminhos_anexos:
        try:
            with open(caminho, "rb") as f:
                anexo_base64 = base64.b64encode(f.read()).decode("ascii")
            anexos_graph.append(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": caminho.rsplit("/", 1)[-1],
                    "contentType": "application/octet-stream",
                    "contentBytes": anexo_base64,
                }
            )
        except OSError as erro:
            logger.warning("Não foi possível ler o anexo %s: %s", caminho, erro)

    protocolo_assunto = f" — Protocolo {protocolo}" if protocolo else ""
    corpo = {
        "message": {
            "subject": f"Nova mensagem recebida{protocolo_assunto}: {assunto}",
            "body": {
                "contentType": "HTML",
                "content": _montar_corpo_mensagem_html(remetente_nome, assunto, conteudo, protocolo),
            },
            "toRecipients": [{"emailAddress": {"address": destinatario_email}}],
        },
        "saveToSentItems": True,
    }

    if anexos_graph:
        corpo["message"]["attachments"] = anexos_graph

    try:
        resposta = requests.post(
            GRAPH_SEND_MAIL_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=corpo,
            timeout=20,
        )
        if resposta.status_code == 202:
            logger.info("E-mail (Outlook/Graph) de nova mensagem enviado para %s.", destinatario_email)
            return True, None

        motivo = f"HTTP {resposta.status_code}: {resposta.text[:300]}"
        logger.warning("Falha ao enviar e-mail via Graph: %s", motivo)
        return False, motivo
    except requests.RequestException as erro:
        logger.exception("Falha de rede ao enviar e-mail via Graph")
        return False, f"{type(erro).__name__}: {erro}"
