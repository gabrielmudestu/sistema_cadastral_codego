import base64
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings
from app.schemas.anexo_viii_d import AnexoViiiDCreate, SOLICITACOES_ANEXO_VIII_D

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _carregar_brasao_base64() -> str:
    caminho = os.path.join(TEMPLATES_DIR, "assets", "brasao_codego.png")
    with open(caminho, "rb") as f:
        conteudo = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{conteudo}"


_BRASAO_DATA_URI = _carregar_brasao_base64()


def _formatar_cnpj(digits: str) -> str:
    if len(digits) != 14:
        return digits
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def _formatar_cpf(digits: str) -> str:
    if len(digits) != 11:
        return digits
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _formatar_telefone(digits: str) -> str:
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return digits


def gerar_pdf_anexo_viii_d(dados: AnexoViiiDCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VIII-D (Formulário para pedido de Anuência para
    Alienação entre Particulares) preenchido com os dados reais do requerimento,
    e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_viii_d.html")

    # Monta a lista de solicitações marcadas, na ordem original do documento,
    # substituindo "Outros" pelo texto livre informado.
    itens_solicitacao = []
    for chave, rotulo in SOLICITACOES_ANEXO_VIII_D.items():
        if chave not in dados.solicitacoes:
            continue
        if chave == "outros":
            itens_solicitacao.append(f"Outros: {dados.outros_texto}")
        else:
            itens_solicitacao.append(rotulo)

    html_renderizado = template.render(
        brasao_data_uri=_BRASAO_DATA_URI,
        protocolo=protocolo,
        processo_numero=dados.processo_numero,
        nome_empresarial=dados.nome_empresarial,
        cnpj=_formatar_cnpj(dados.cnpj),
        endereco=dados.endereco,
        telefone=_formatar_telefone(dados.telefone),
        email=dados.email,
        cidade_data=datetime.now().strftime("Goiânia, %d/%m/%Y"),
        representante_nome=dados.representante_nome,
        representante_estado_civil=dados.representante_estado_civil,
        representante_rg=dados.representante_rg,
        representante_cpf=_formatar_cpf(dados.representante_cpf),
        representante_endereco=dados.representante_endereco,
        itens_solicitacao=itens_solicitacao,
        motivacao=dados.motivacao,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_viii_d.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo
