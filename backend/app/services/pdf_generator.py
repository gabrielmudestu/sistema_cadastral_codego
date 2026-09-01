import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def gerar_pdf_anexo_viii_d(usuario, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VIII-D preenchido com os dados do usuário
    e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_viii_d.html")
    html_renderizado = template.render(
        nome_empresarial=usuario.nome,
        cnpj=usuario.cpf_cnpj,
        endereco="",  # a coletar em versão futura do formulário, se necessário
        telefone=usuario.telefone,
        email=usuario.email,
        cidade_data=datetime.now().strftime("Goiânia, %d/%m/%Y"),
        protocolo=protocolo,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_viii_d.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo
