import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.config import settings

logger = logging.getLogger("codego.email")


def _montar_corpo_texto(nome_empresarial: str, protocolo: str) -> str:
    return (
        f"Olá,\n\n"
        f"Confirmamos o recebimento do documento assinado referente ao processo de "
        f"{nome_empresarial}.\n\n"
        f"Protocolo: {protocolo}\n\n"
        f"Este e-mail confirma que o arquivo foi recebido e validado pelo Sistema "
        f"Cadastral CODEGO. Em breve o recibo eletrônico deste processo estará "
        f"disponível.\n\n"
        f"Atenciosamente,\n"
        f"Companhia de Desenvolvimento Econômico de Goiás"
    )


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


def enviar_email_documento_assinado(
    destinatario_email: str,
    nome_empresarial: str,
    protocolo: str,
    caminho_pdf_assinado: str,
) -> bool:
    """
    Envia um e-mail de confirmação de recebimento do documento assinado, com o
    PDF assinado em anexo. Retorna True se o envio foi bem-sucedido, False caso
    contrário (nunca levanta exceção — falha de e-mail não deve derrubar o
    upload, que já foi salvo com sucesso).
    """
    if not settings.smtp_enabled:
        logger.info("Envio de e-mail desabilitado (SMTP_ENABLED=false). Pulando envio.")
        return False

    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP_USER/SMTP_PASSWORD não configurados. Pulando envio de e-mail.")
        return False

    mensagem = MIMEMultipart("mixed")
    mensagem["Subject"] = f"Documento assinado recebido — Protocolo {protocolo}"
    mensagem["From"] = formataddr((settings.smtp_from_name, settings.smtp_user))
    mensagem["To"] = destinatario_email

    corpo_alternativo = MIMEMultipart("alternative")
    corpo_alternativo.attach(MIMEText(_montar_corpo_texto(nome_empresarial, protocolo), "plain", "utf-8"))
    corpo_alternativo.attach(MIMEText(_montar_corpo_html(nome_empresarial, protocolo), "html", "utf-8"))
    mensagem.attach(corpo_alternativo)

    try:
        with open(caminho_pdf_assinado, "rb") as f:
            anexo = MIMEApplication(f.read(), _subtype="pdf")
            anexo.add_header(
                "Content-Disposition", "attachment", filename=f"{protocolo}_assinado.pdf"
            )
            mensagem.attach(anexo)
    except OSError as erro:
        logger.warning("Não foi possível anexar o PDF assinado ao e-mail: %s", erro)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as servidor:
            if settings.smtp_use_tls:
                servidor.starttls()
            servidor.login(settings.smtp_user, settings.smtp_password)
            servidor.sendmail(settings.smtp_user, [destinatario_email], mensagem.as_string())
        logger.info("E-mail de confirmação enviado para %s (protocolo %s).", destinatario_email, protocolo)
        return True
    except Exception as erro:  # noqa: BLE001 — falha de e-mail não pode derrubar o upload
        logger.warning("Falha ao enviar e-mail de confirmação: %s", erro)
        return False
