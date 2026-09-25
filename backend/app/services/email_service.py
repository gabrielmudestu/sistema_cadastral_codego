import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from app.config import settings

logger = logging.getLogger("codego.email")


def _adicionar_cabecalhos_padrao(mensagem: MIMEMultipart, remetente: str) -> None:
    """
    Date e Message-ID: o smtplib não os adiciona sozinho, e e-mail sem eles
    é tratado como suspeito pelos filtros de spam (Gmail, Outlook).
    """
    mensagem["Date"] = formatdate(localtime=True)
    mensagem["Message-ID"] = make_msgid(domain=remetente.split("@")[-1])


def enviar_email_documento_assinado(
    destinatario_email: str,
    nome_empresarial: str,
    protocolo: str,
    caminho_pdf_assinado: str,
    documentos_recebidos: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Envia um e-mail de confirmação de recebimento do documento assinado, com o
    PDF assinado em anexo e a lista dos documentos que acompanham o
    requerimento (só os nomes; os arquivos ficam no sistema). Escolhe a implementação conforme
    settings.email_provider ("smtp" ou "outlook_graph"). Retorna (True, None)
    se o envio foi bem-sucedido, ou (False, mensagem_de_erro) caso contrário —
    nunca levanta exceção, já que falha de e-mail não deve derrubar o upload,
    que já foi salvo com sucesso.
    """
    if settings.email_provider == "outlook_graph":
        from app.services.outlook_email_service import enviar_email_documento_assinado_outlook

        return enviar_email_documento_assinado_outlook(
            destinatario_email, nome_empresarial, protocolo, caminho_pdf_assinado, documentos_recebidos
        )

    return _enviar_via_smtp(
        destinatario_email, nome_empresarial, protocolo, caminho_pdf_assinado, documentos_recebidos
    )


def enviar_email_nova_mensagem(
    destinatario_email: str,
    remetente_nome: str,
    assunto: str,
    conteudo: str,
    protocolo: str | None,
    caminhos_anexos: list[str],
) -> tuple[bool, str | None]:
    """
    Envia um e-mail de notificação para uma nova mensagem recebida no Módulo
    de Mensagens e Anexos (Etapa 4), com os anexos (se houver) em anexo.
    Escolhe a implementação conforme settings.email_provider ("smtp" ou
    "outlook_graph"). Retorna (True, None) se o envio foi bem-sucedido, ou
    (False, mensagem_de_erro) caso contrário — nunca levanta exceção.
    """
    if settings.email_provider == "outlook_graph":
        from app.services.outlook_email_service import enviar_email_nova_mensagem_outlook

        return enviar_email_nova_mensagem_outlook(
            destinatario_email, remetente_nome, assunto, conteudo, protocolo, caminhos_anexos
        )

    return _enviar_mensagem_via_smtp(
        destinatario_email, remetente_nome, assunto, conteudo, protocolo, caminhos_anexos
    )


def enviar_email_protocolo(
    destinatario_email: str,
    nome_empresarial: str,
    nome_documento: str,
    protocolo: str,
    caminho_pdf: str,
) -> tuple[bool, str | None]:
    """
    Envia para quem preencheu o formulário o número de protocolo do processo
    recém-aberto, com o PDF gerado (ainda não assinado) em anexo — assim a
    pessoa não perde o protocolo se fechar a tela sem anotá-lo. Escolhe a
    implementação conforme settings.email_provider ("smtp" ou "outlook_graph").
    Retorna (True, None) se o envio foi bem-sucedido, ou (False, mensagem_de_erro)
    caso contrário — nunca levanta exceção, já que falha de e-mail não deve
    impedir a geração do documento.
    """
    if settings.email_provider == "outlook_graph":
        from app.services.outlook_email_service import enviar_email_protocolo_outlook

        return enviar_email_protocolo_outlook(
            destinatario_email, nome_empresarial, nome_documento, protocolo, caminho_pdf
        )

    return _enviar_protocolo_via_smtp(destinatario_email, nome_empresarial, nome_documento, protocolo, caminho_pdf)


def montar_corpo_protocolo_texto(nome_empresarial: str, nome_documento: str, protocolo: str) -> str:
    return (
        f"Olá,\n\n"
        f"Recebemos o preenchimento do documento \"{nome_documento}\" referente a "
        f"{nome_empresarial}.\n\n"
        f"Seu número de protocolo é: {protocolo}\n\n"
        f"Guarde este número: ele é necessário para enviar o documento assinado, "
        f"consultar o recibo eletrônico e enviar mensagens sobre este processo.\n\n"
        f"Próximo passo: assine o documento em anexo e envie-o no Sistema Cadastral "
        f"CODEGO, na opção \"Enviar documento assinado\" da página inicial, "
        f"informando o protocolo acima.\n\n"
        f"Atenciosamente,\n"
        f"Companhia de Desenvolvimento Econômico de Goiás"
    )


def montar_corpo_protocolo_html(nome_empresarial: str, nome_documento: str, protocolo: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; color: #1a1a1a; font-size: 14px; line-height: 1.6;">
      <p>Olá,</p>
      <p>
        Recebemos o preenchimento do documento <strong>{nome_documento}</strong>
        referente a <strong>{nome_empresarial}</strong>.
      </p>
      <p>Seu número de protocolo é:</p>
      <p style="font-family: monospace; font-size: 20px; background: #f2f2f2; padding: 10px 16px; display: inline-block;">
        <strong>{protocolo}</strong>
      </p>
      <p>
        <strong>Guarde este número:</strong> ele é necessário para enviar o documento
        assinado, consultar o recibo eletrônico e enviar mensagens sobre este processo.
      </p>
      <p>
        <strong>Próximo passo:</strong> assine o documento em anexo e envie-o no
        <strong>Sistema Cadastral CODEGO</strong>, na opção "Enviar documento assinado"
        da página inicial, informando o protocolo acima.
      </p>
      <p>Atenciosamente,<br>Companhia de Desenvolvimento Econômico de Goiás</p>
    </div>
    """


def _montar_corpo_texto(nome_empresarial: str, protocolo: str, documentos_recebidos: list[str] | None = None) -> str:
    lista_documentos = (
        "Documentos anexados ao requerimento:\n"
        + "".join(f"- {descricao}\n" for descricao in documentos_recebidos)
        + "\n"
        if documentos_recebidos
        else ""
    )
    return (
        f"Olá,\n\n"
        f"Confirmamos o recebimento do documento assinado referente ao processo de "
        f"{nome_empresarial}.\n\n"
        f"Protocolo: {protocolo}\n\n"
        f"{lista_documentos}"
        f"Este e-mail confirma que o arquivo foi recebido e validado pelo Sistema "
        f"Cadastral CODEGO. Em breve o recibo eletrônico deste processo estará "
        f"disponível.\n\n"
        f"Atenciosamente,\n"
        f"Companhia de Desenvolvimento Econômico de Goiás"
    )


def _montar_lista_documentos_html(documentos_recebidos: list[str] | None) -> str:
    if not documentos_recebidos:
        return ""
    itens = "".join(f"<li>{descricao}</li>" for descricao in documentos_recebidos)
    return f"<p><strong>Documentos anexados ao requerimento:</strong></p><ul>{itens}</ul>"


def _montar_corpo_html(nome_empresarial: str, protocolo: str, documentos_recebidos: list[str] | None = None) -> str:
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
      {_montar_lista_documentos_html(documentos_recebidos)}
      <p>
        Este e-mail confirma que o arquivo foi recebido e validado pelo
        <strong>Sistema Cadastral CODEGO</strong>. Em breve o recibo eletrônico
        deste processo estará disponível.
      </p>
      <p>Atenciosamente,<br>Companhia de Desenvolvimento Econômico de Goiás</p>
    </div>
    """


def _montar_corpo_mensagem_texto(remetente_nome: str, assunto: str, conteudo: str, protocolo: str | None) -> str:
    linha_protocolo = f"Protocolo vinculado: {protocolo}\n\n" if protocolo else "Sem protocolo vinculado.\n\n"
    return (
        f"Olá,\n\n"
        f"Uma nova mensagem foi recebida no Sistema Cadastral CODEGO.\n\n"
        f"Remetente: {remetente_nome}\n"
        f"Assunto: {assunto}\n\n"
        f"{linha_protocolo}"
        f"Mensagem:\n{conteudo}\n\n"
        f"Atenciosamente,\n"
        f"Sistema Cadastral CODEGO"
    )


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


def _enviar_via_smtp(
    destinatario_email: str,
    nome_empresarial: str,
    protocolo: str,
    caminho_pdf_assinado: str,
    documentos_recebidos: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Envia um e-mail de confirmação de recebimento do documento assinado, com o
    PDF assinado em anexo. Retorna (True, None) se o envio foi bem-sucedido, ou
    (False, mensagem_de_erro) caso contrário — nunca levanta exceção, já que
    falha de e-mail não deve derrubar o upload, que já foi salvo com sucesso.
    """
    if not settings.smtp_enabled:
        motivo = "Envio de e-mail desabilitado (SMTP_ENABLED=false)."
        logger.info(motivo)
        return False, motivo

    if not settings.smtp_user or not settings.smtp_password:
        motivo = "SMTP_USER/SMTP_PASSWORD não configurados."
        logger.warning(motivo)
        return False, motivo

    remetente = settings.smtp_from_email or settings.smtp_user

    mensagem = MIMEMultipart("mixed")
    mensagem["Subject"] = f"Documento assinado recebido — Protocolo {protocolo}"
    mensagem["From"] = formataddr((settings.smtp_from_name, remetente))
    mensagem["To"] = destinatario_email
    _adicionar_cabecalhos_padrao(mensagem, remetente)

    corpo_alternativo = MIMEMultipart("alternative")
    corpo_alternativo.attach(MIMEText(_montar_corpo_texto(nome_empresarial, protocolo, documentos_recebidos), "plain", "utf-8"))
    corpo_alternativo.attach(MIMEText(_montar_corpo_html(nome_empresarial, protocolo, documentos_recebidos), "html", "utf-8"))
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
            servidor.sendmail(remetente, [destinatario_email], mensagem.as_string())
        logger.info("E-mail de confirmação enviado para %s (protocolo %s).", destinatario_email, protocolo)
        return True, None
    except Exception as erro:  # noqa: BLE001 — falha de e-mail não pode derrubar o upload
        logger.exception("Falha ao enviar e-mail de confirmação")
        return False, f"{type(erro).__name__}: {erro}"


def _enviar_protocolo_via_smtp(
    destinatario_email: str,
    nome_empresarial: str,
    nome_documento: str,
    protocolo: str,
    caminho_pdf: str,
) -> tuple[bool, str | None]:
    """
    Envia o e-mail com o número de protocolo e o PDF gerado em anexo. Retorna
    (True, None) se o envio foi bem-sucedido, ou (False, mensagem_de_erro) caso
    contrário — nunca levanta exceção.
    """
    if not settings.smtp_enabled:
        motivo = "Envio de e-mail desabilitado (SMTP_ENABLED=false)."
        logger.info(motivo)
        return False, motivo

    if not settings.smtp_user or not settings.smtp_password:
        motivo = "SMTP_USER/SMTP_PASSWORD não configurados."
        logger.warning(motivo)
        return False, motivo

    remetente = settings.smtp_from_email or settings.smtp_user

    mensagem = MIMEMultipart("mixed")
    mensagem["Subject"] = f"Seu protocolo {protocolo} — {nome_documento}"
    mensagem["From"] = formataddr((settings.smtp_from_name, remetente))
    mensagem["To"] = destinatario_email
    _adicionar_cabecalhos_padrao(mensagem, remetente)

    corpo_alternativo = MIMEMultipart("alternative")
    corpo_alternativo.attach(
        MIMEText(montar_corpo_protocolo_texto(nome_empresarial, nome_documento, protocolo), "plain", "utf-8")
    )
    corpo_alternativo.attach(
        MIMEText(montar_corpo_protocolo_html(nome_empresarial, nome_documento, protocolo), "html", "utf-8")
    )
    mensagem.attach(corpo_alternativo)

    try:
        with open(caminho_pdf, "rb") as f:
            anexo = MIMEApplication(f.read(), _subtype="pdf")
            anexo.add_header("Content-Disposition", "attachment", filename=f"{protocolo}.pdf")
            mensagem.attach(anexo)
    except OSError as erro:
        logger.warning("Não foi possível anexar o PDF gerado ao e-mail: %s", erro)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as servidor:
            if settings.smtp_use_tls:
                servidor.starttls()
            servidor.login(settings.smtp_user, settings.smtp_password)
            servidor.sendmail(remetente, [destinatario_email], mensagem.as_string())
        logger.info("E-mail de protocolo enviado para %s (protocolo %s).", destinatario_email, protocolo)
        return True, None
    except Exception as erro:  # noqa: BLE001 — falha de e-mail não pode impedir a geração do documento
        logger.exception("Falha ao enviar e-mail de protocolo")
        return False, f"{type(erro).__name__}: {erro}"


def _enviar_mensagem_via_smtp(
    destinatario_email: str,
    remetente_nome: str,
    assunto: str,
    conteudo: str,
    protocolo: str | None,
    caminhos_anexos: list[str],
) -> tuple[bool, str | None]:
    """
    Envia o e-mail de notificação de nova mensagem, com os anexos (se houver)
    anexados separadamente. Retorna (True, None) se o envio foi bem-sucedido,
    ou (False, mensagem_de_erro) caso contrário — nunca levanta exceção.
    """
    if not settings.smtp_enabled:
        motivo = "Envio de e-mail desabilitado (SMTP_ENABLED=false)."
        logger.info(motivo)
        return False, motivo

    if not settings.smtp_user or not settings.smtp_password:
        motivo = "SMTP_USER/SMTP_PASSWORD não configurados."
        logger.warning(motivo)
        return False, motivo

    remetente = settings.smtp_from_email or settings.smtp_user

    mensagem = MIMEMultipart("mixed")
    protocolo_assunto = f" — Protocolo {protocolo}" if protocolo else ""
    mensagem["Subject"] = f"Nova mensagem recebida{protocolo_assunto}: {assunto}"
    mensagem["From"] = formataddr((settings.smtp_from_name, remetente))
    mensagem["To"] = destinatario_email
    _adicionar_cabecalhos_padrao(mensagem, remetente)

    corpo_alternativo = MIMEMultipart("alternative")
    corpo_alternativo.attach(
        MIMEText(_montar_corpo_mensagem_texto(remetente_nome, assunto, conteudo, protocolo), "plain", "utf-8")
    )
    corpo_alternativo.attach(
        MIMEText(_montar_corpo_mensagem_html(remetente_nome, assunto, conteudo, protocolo), "html", "utf-8")
    )
    mensagem.attach(corpo_alternativo)

    for caminho in caminhos_anexos:
        try:
            with open(caminho, "rb") as f:
                subtipo = caminho.rsplit(".", 1)[-1].lower() if "." in caminho else "octet-stream"
                anexo = MIMEApplication(f.read(), _subtype=subtipo)
                anexo.add_header(
                    "Content-Disposition", "attachment", filename=caminho.rsplit("/", 1)[-1]
                )
                mensagem.attach(anexo)
        except OSError as erro:
            logger.warning("Não foi possível anexar o arquivo %s ao e-mail: %s", caminho, erro)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as servidor:
            if settings.smtp_use_tls:
                servidor.starttls()
            servidor.login(settings.smtp_user, settings.smtp_password)
            servidor.sendmail(remetente, [destinatario_email], mensagem.as_string())
        logger.info("E-mail de nova mensagem enviado para %s.", destinatario_email)
        return True, None
    except Exception as erro:  # noqa: BLE001 — falha de e-mail não pode derrubar o envio da mensagem
        logger.exception("Falha ao enviar e-mail de nova mensagem")
        return False, f"{type(erro).__name__}: {erro}"
