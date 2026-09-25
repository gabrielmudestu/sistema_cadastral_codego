import base64
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings
from app.schemas.anexo_viii_d import AnexoViiiDCreate, SOLICITACOES_ANEXO_VIII_D
from app.schemas.anexo_viii_a import AnexoViiiACreate
from app.schemas.anexo_viii_b import AnexoViiiBCreate
from app.schemas.anexo_viii_c import AnexoViiiCCreate
from app.schemas.anexo_iii import AnexoIiiCreate, DOCUMENTOS_ANEXO_III, MAX_CNAES
from app.schemas.anexo_v_declaracao_uso import AnexoVDeclaracaoUsoCreate
from app.schemas.anexo_v_cfo import AnexoVCfoCreate
from app.schemas.anexo_vii_mce import AnexoViiMceCreate, MCE_ESTRUTURA
from app.schemas.anexo_ix import AnexoIXCreate
from app.schemas.anexo_vi_evtf import AnexoVIEvtfCreate

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _carregar_imagem_base64(nome_arquivo: str) -> str:
    caminho = os.path.join(TEMPLATES_DIR, "assets", nome_arquivo)
    with open(caminho, "rb") as f:
        conteudo = base64.b64encode(f.read()).decode("ascii")
    tipo = "jpeg" if nome_arquivo.lower().endswith((".jpg", ".jpeg")) else "png"
    return f"data:image/{tipo};base64,{conteudo}"


_BRASAO_DATA_URI = _carregar_imagem_base64("brasao_codego.png")
# Logo usado no cabeçalho das páginas do Regulamento (extraído do modelo oficial).
_LOGO_REGULAMENTO_DATA_URI = _carregar_imagem_base64("logo_codego_regulamento.png")


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


def _formatar_cep(digits: str) -> str:
    if len(digits) != 8:
        return digits
    return f"{digits[:5]}-{digits[5:]}"


MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def _data_por_extenso(data: datetime) -> str:
    return f"{data.day:02d} de {MESES_PT[data.month - 1]} de {data.year}"


def _mes_ano_por_extenso(mes_ano: str) -> str:
    """'2026-09' -> 'setembro/2026'"""
    ano, mes = mes_ano.split("-")
    return f"{MESES_PT[int(mes) - 1]}/{ano}"


def _formatar_percentual(valor: float) -> str:
    if not valor:
        return ""
    return f"{valor:g}%".replace(".", ",")


def gerar_pdf_anexo_viii_d(dados: AnexoViiiDCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VIII-D (Formulário para pedido de Anuência para
    Alienação entre Particulares) preenchido com os dados reais do requerimento,
    e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_viii_d.html")

    # Monta a lista de solicitações marcadas, na ordem original do documento.
    # O item "Outros" é marcado à parte para ser desenhado como uma linha
    # preenchida (sublinhado), no mesmo espírito do "Outros:____________"
    # do modelo original.
    itens_solicitacao = []
    for chave, rotulo in SOLICITACOES_ANEXO_VIII_D.items():
        if chave not in dados.solicitacoes:
            continue
        if chave == "outros":
            itens_solicitacao.append({"texto": "Outros:", "valor_linha": dados.outros_texto})
        else:
            itens_solicitacao.append({"texto": rotulo, "valor_linha": None})

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


def gerar_pdf_anexo_viii_a(dados: AnexoViiiACreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VIII-A (Formulário de Pedido de Anuência para
    Alienação entre Particulares) preenchido com os dados reais do requerimento,
    e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_viii_a.html")

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
        area_via=dados.area_via,
        area_modulos=dados.area_modulos,
        area_quadra=dados.area_quadra,
        area_distrito=dados.area_distrito,
        comprador_nome_empresarial=dados.comprador_nome_empresarial,
        comprador_cnpj=_formatar_cnpj(dados.comprador_cnpj),
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_viii_a.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo


def gerar_pdf_anexo_iii(dados: AnexoIiiCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo III (Solicitação de Área) preenchido com os
    dados reais do requerimento, reproduzindo o layout do modelo do Regulamento,
    e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_iii.html")

    # Check list na ordem original do documento, marcando o que foi informado
    # como anexado ao requerimento.
    documentos = [
        {"texto": rotulo, "marcado": chave in dados.documentos}
        for chave, rotulo in DOCUMENTOS_ANEXO_III.items()
    ]

    # O modelo sempre tem as 4 linhas de CNAE numeradas; as não usadas ficam em branco.
    cnaes = [{"numero": c.numero, "descricao": c.descricao} for c in dados.cnaes]
    cnaes += [{"numero": "", "descricao": ""}] * (MAX_CNAES - len(cnaes))

    html_renderizado = template.render(
        logo_data_uri=_LOGO_REGULAMENTO_DATA_URI,
        protocolo=protocolo,
        municipio_interesse=dados.municipio_interesse,
        metragem_necessaria=dados.metragem_necessaria,
        nome_empresarial=dados.nome_empresarial,
        cnpj=_formatar_cnpj(dados.cnpj),
        endereco_correspondencia_empresa=dados.endereco_correspondencia_empresa,
        representante_nome=dados.representante_nome,
        representante_cpf=_formatar_cpf(dados.representante_cpf),
        representante_rg=dados.representante_rg,
        representante_nome_mae=dados.representante_nome_mae,
        email=dados.email,
        telefones=dados.telefones,
        representante_endereco_correspondencia=dados.representante_endereco_correspondencia,
        cnaes=cnaes,
        documentos=documentos,
        cidade_data=f"Goiânia, {_data_por_extenso(datetime.now())}.",
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_iii.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    # base_url aponta para a pasta de templates para o @font-face achar as
    # fontes em assets/fonts.
    HTML(string=html_renderizado, base_url=TEMPLATES_DIR).write_pdf(caminho_completo)

    return caminho_completo


# Faixa do cabeçalho das páginas do Anexo V no Regulamento (verde, com os
# logos da CODEGO e do Governo de Goiás), extraída do modelo oficial.
_FAIXA_REGULAMENTO_ANEXO_V_DATA_URI = _carregar_imagem_base64("faixa_regulamento_anexo_v.jpg")


def gerar_pdf_anexo_v_declaracao_uso(dados: AnexoVDeclaracaoUsoCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo V (Declaração de Uso da Rede de Abastecimento
    de Água e de Esgoto da CODEGO) preenchido com os dados reais do requerimento,
    reproduzindo o layout do modelo do Regulamento, e gera o PDF em disco.
    Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_v_declaracao_uso.html")

    html_renderizado = template.render(
        faixa_data_uri=_FAIXA_REGULAMENTO_ANEXO_V_DATA_URI,
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
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_v_declaracao_uso.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    # base_url aponta para a pasta de templates para o @font-face achar as
    # fontes em assets/fonts.
    HTML(string=html_renderizado, base_url=TEMPLATES_DIR).write_pdf(caminho_completo)

    return caminho_completo


# Medidas da tabela do "Modelo do Cronograma" do Regulamento (em pt): largura
# total, coluna de serviços e quantidade de meses por tabela (4 trimestres, para
# uma obra de até 1 ano caber numa tabela só). Cronogramas mais longos
# continuam em novas tabelas.
LARGURA_TABELA_CFO = 589.6
LARGURA_COLUNA_SERVICO_CFO = 122.3
MESES_POR_BLOCO_CFO = 12



def gerar_pdf_anexo_v_cfo(dados: AnexoVCfoCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo V (Cronograma Físico da Obra — CFO) preenchido
    com os dados reais do requerimento, reproduzindo o layout do modelo do
    Regulamento, e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_v_cfo.html")

    total = len(dados.servicos[0].percentuais)
    meses = [{"rotulo": f"{i + 1}º mês"} for i in range(total)]

    # As colunas de mês ocupam toda a largura da tabela do modelo. Quando o
    # cronograma passa de um bloco, todos os blocos usam a largura do bloco
    # cheio (o último pode ficar mais estreito).
    meses_por_coluna = min(total, MESES_POR_BLOCO_CFO)
    largura_mes = round((LARGURA_TABELA_CFO - LARGURA_COLUNA_SERVICO_CFO) / meses_por_coluna, 2)

    # Monta os blocos (tabelas) com os cabeçalhos de trimestre e as linhas de
    # serviço já formatadas, para o template só precisar iterar.
    blocos = []
    for inicio_bloco in range(0, total, MESES_POR_BLOCO_CFO):
        fim_bloco = min(inicio_bloco + MESES_POR_BLOCO_CFO, total)
        trimestres = [
            {
                "rotulo": f"{t // 3 + 1}º Trimestre",
                "colunas": min(t + 3, fim_bloco) - t,
            }
            for t in range(inicio_bloco, fim_bloco, 3)
        ]
        linhas = [
            {
                "descricao": servico.descricao,
                "celulas": [_formatar_percentual(p) for p in servico.percentuais[inicio_bloco:fim_bloco]],
            }
            for servico in dados.servicos
        ]
        blocos.append({
            "meses": meses[inicio_bloco:fim_bloco],
            "trimestres": trimestres,
            "linhas": linhas,
            "largura_mes": largura_mes,
            "largura": round(LARGURA_COLUNA_SERVICO_CFO + largura_mes * (fim_bloco - inicio_bloco), 2),
        })

    html_renderizado = template.render(
        logo_data_uri=_LOGO_REGULAMENTO_DATA_URI,
        protocolo=protocolo,
        nome_empresa=dados.nome_empresa,
        endereco=dados.endereco,
        area_empresa=dados.area_empresa,
        area_construida=dados.area_construida,
        inicio_obras=_mes_ano_por_extenso(dados.inicio_obras),
        termino_obras=_mes_ano_por_extenso(dados.termino_obras),
        blocos=blocos,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_v_cfo.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    # base_url aponta para a pasta de templates para o @font-face achar as
    # fontes em assets/fonts.
    HTML(string=html_renderizado, base_url=TEMPLATES_DIR).write_pdf(caminho_completo)

    return caminho_completo


# Papel timbrado do modelo do MCE (logos, marca d'água, endereço e bandeira),
# extraído do PDF oficial.
_FUNDO_MCE_DATA_URI = _carregar_imagem_base64("fundo_mce_codego.png")


def gerar_pdf_anexo_vii_mce(dados: AnexoViiMceCreate, protocolo: str) -> str:
    """
    Renderiza o template do Memorial de Caracterização do Empreendimento (MCE)
    preenchido com os dados reais do requerimento, reproduzindo o layout do
    modelo da CODEGO (Rev. 2), e gera o PDF em disco. Retorna o caminho do
    arquivo gerado.
    """
    template = _env.get_template("anexo_vii_mce.html")

    valores = dados.model_dump()
    valores["cnpj"] = _formatar_cnpj(dados.cnpj)
    valores["cep"] = _formatar_cep(dados.cep)
    valores["telefone"] = _formatar_telefone(dados.telefone)
    valores["mao_obra_total"] = dados.mao_obra_total
    for campo in ("area_total_terreno", "area_construida", "area_verde"):
        if valores[campo]:
            valores[campo] = f"{valores[campo]} m²"
    if dados.previsao_funcionamento:
        valores["previsao_funcionamento"] = _mes_ano_por_extenso(dados.previsao_funcionamento)
    for campo in ("data_inicio_operacoes", "pca_data_revisao"):
        if valores[campo]:
            valores[campo] = datetime.strptime(valores[campo], "%Y-%m-%d").strftime("%d/%m/%Y")

    # Resolve a estrutura do MCE com os valores preenchidos. Campos opcionais
    # deixados em branco aparecem como "Não informado" no documento.
    secoes = []
    for secao in MCE_ESTRUTURA:
        subsecoes = []
        for subsecao in secao["subsecoes"]:
            itens = []
            for campo, rotulo in subsecao["campos"]:
                valor = valores[campo]
                if isinstance(valor, str):
                    valor = valor.strip()
                itens.append({"rotulo": rotulo, "valor": valor if valor != "" else "Não informado"})
            subsecoes.append({**subsecao, "itens": itens})
        secoes.append({"titulo": secao["titulo"], "subsecoes": subsecoes})

    html_renderizado = template.render(
        fundo_data_uri=_FUNDO_MCE_DATA_URI,
        protocolo=protocolo,
        secoes=secoes,
        local=dados.local_cidade_uf,
        data=_data_por_extenso(datetime.now()),
        responsavel_nome=dados.responsavel_nome,
        responsavel_cargo=dados.responsavel_cargo,
        razao_social=dados.razao_social,
        cnpj=_formatar_cnpj(dados.cnpj),
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_vii_mce.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo


def gerar_pdf_anexo_viii_b(dados: AnexoViiiBCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VIII-B (Pedido de Anuência para Remembramento/
    Desmembramento de Área) preenchido com os dados reais do requerimento, e gera
    o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_viii_b.html")

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
        tipo_operacao=dados.tipo_operacao,
        area_via=dados.area_via,
        area_modulos=dados.area_modulos,
        area_quadra=dados.area_quadra,
        area_distrito=dados.area_distrito,
        area_total_m2=dados.area_total_m2,
        justificativa=dados.justificativa,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_viii_b.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo


def gerar_pdf_anexo_viii_c(dados: AnexoViiiCCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VIII-C (Pedido de Anuência para Fusão, Cisão,
    Incorporação, Mudança do Quadro Societário, Mudança da Atividade Econômica e
    demais alterações do Contrato Social) preenchido com os dados reais do
    requerimento, e gera o PDF em disco. Retorna o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_viii_c.html")

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
        tipo_alteracao=dados.tipo_alteracao,
        outra_alteracao_texto=dados.outra_alteracao_texto,
        justificativa=dados.justificativa,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_viii_c.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo


def gerar_pdf_anexo_ix(dados: AnexoIXCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo IX (Formulário de Atualização Cadastral Anual)
    preenchido com os dados reais do requerimento, e gera o PDF em disco. Retorna
    o caminho do arquivo gerado.
    """
    template = _env.get_template("anexo_ix.html")

    html_renderizado = template.render(
        brasao_data_uri=_BRASAO_DATA_URI,
        protocolo=protocolo,
        cidade_data=datetime.now().strftime("Goiânia, %d/%m/%Y"),
        tecnico_responsavel=dados.tecnico_responsavel,
        nome_empresarial=dados.nome_empresarial,
        cnpj=_formatar_cnpj(dados.cnpj),
        endereco=dados.endereco,
        distrito=dados.distrito,
        telefone=_formatar_telefone(dados.telefone),
        email=dados.email,
        responsavel=dados.responsavel,
        num_funcionarios=dados.num_funcionarios,
        num_matriculas_imovel=dados.num_matriculas_imovel,
        area_total_m2=dados.area_total_m2,
        area_ocupada_m2=dados.area_ocupada_m2,
        taxa_ocupacao=dados.taxa_ocupacao,
        asfalto_frente=dados.asfalto_frente,
        status_operacao=dados.status_operacao,
        status_operacao_prazo_dias=dados.status_operacao_prazo_dias,
        status_operacao_paralisada_mes=dados.status_operacao_paralisada_mes,
        status_operacao_outro_texto=dados.status_operacao_outro_texto,
        possui_hidrometro=dados.possui_hidrometro,
        hidrometro_quantos=dados.hidrometro_quantos,
        hidrometro_1_numero=dados.hidrometro_1_numero,
        hidrometro_1_faturamento=dados.hidrometro_1_faturamento,
        hidrometro_2_numero=dados.hidrometro_2_numero,
        hidrometro_2_faturamento=dados.hidrometro_2_faturamento,
        possui_poco_artesiano=dados.possui_poco_artesiano,
        poco_possui_outorga=dados.poco_possui_outorga,
        outorga_vigencia=dados.outorga_vigencia,
        outorga_vazao=dados.outorga_vazao,
        responsavel_abastecimento=dados.responsavel_abastecimento,
        responsavel_abastecimento_municipio=dados.responsavel_abastecimento_municipio,
        possui_ete=dados.possui_ete,
        ete_ativa=dados.ete_ativa,
        possui_medidor_vazao=dados.possui_medidor_vazao,
        medidor_vazao_outro_texto=dados.medidor_vazao_outro_texto,
        responsavel_esgoto=dados.responsavel_esgoto,
        responsavel_esgoto_outro_texto=dados.responsavel_esgoto_outro_texto,
        licenca_previa=dados.licenca_previa,
        licenca_previa_vigencia=dados.licenca_previa_vigencia,
        licenca_instalacao=dados.licenca_instalacao,
        licenca_instalacao_vigencia=dados.licenca_instalacao_vigencia,
        licenca_operacao=dados.licenca_operacao,
        licenca_operacao_vigencia=dados.licenca_operacao_vigencia,
        licenciamento_bombeiros=dados.licenciamento_bombeiros,
        licenciamento_bombeiros_vigencia=dados.licenciamento_bombeiros_vigencia,
        certidao_uso_solo=dados.certidao_uso_solo,
        certidao_uso_solo_vigencia=dados.certidao_uso_solo_vigencia,
        alvara_sanitario=dados.alvara_sanitario,
        alvara_sanitario_vigencia=dados.alvara_sanitario_vigencia,
        responsavel_tecnico_nome=dados.responsavel_tecnico_nome,
        responsavel_tecnico_registro=dados.responsavel_tecnico_registro,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_ix.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo


def gerar_pdf_anexo_vi_evtf(dados: AnexoVIEvtfCreate, protocolo: str) -> str:
    """
    Renderiza o template do Anexo VI (Formulário de Viabilidade Técnica e
    Financeira - EVTF) preenchido com os dados reais do requerimento, e gera o
    PDF em disco. Retorna o caminho do arquivo gerado.

    Cobre as seções 1 (Dados Cadastrais), 2 (Dados Econômicos e Financeiros,
    simplificada) e 4 (Concepção do Projeto, sem as tabelas de produção
    anual/mercado/matérias-primas). As seções 3 (DRE), 5 (Investimentos) e 6
    (Custos Anuais) ainda serão adicionadas em uma etapa seguinte.
    """
    template = _env.get_template("anexo_vi_evtf.html")

    html_renderizado = template.render(
        brasao_data_uri=_BRASAO_DATA_URI,
        protocolo=protocolo,
        cidade_data=datetime.now().strftime("Goiânia, %d/%m/%Y"),
        razao_social=dados.razao_social,
        cnpj=_formatar_cnpj(dados.cnpj),
        endereco=dados.endereco,
        cidade=dados.cidade,
        uf=dados.uf,
        cep=dados.cep,
        telefone=_formatar_telefone(dados.telefone),
        email=dados.email,
        conta_corrente=dados.conta_corrente,
        banco=dados.banco,
        agencia=dados.agencia,
        praca_pagamento=dados.praca_pagamento,
        responsavel_nome=dados.responsavel_nome,
        responsavel_ci_orgao=dados.responsavel_ci_orgao,
        responsavel_cpf=_formatar_cpf(dados.responsavel_cpf),
        responsavel_endereco=dados.responsavel_endereco,
        responsavel_cidade_uf=dados.responsavel_cidade_uf,
        responsavel_cep=dados.responsavel_cep,
        responsavel_cargo=dados.responsavel_cargo,
        responsavel_contato=dados.responsavel_contato,
        responsavel_email=dados.responsavel_email,
        ramo_atividade_cnae=dados.ramo_atividade_cnae,
        ramo_atividade_especificacao=dados.ramo_atividade_especificacao,
        capital_social_data=dados.capital_social_data,
        capital_social_ato=dados.capital_social_ato,
        capital_recursos_proprios=dados.capital_recursos_proprios,
        capital_recursos_incentivos=dados.capital_recursos_incentivos,
        capital_recursos_outros=dados.capital_recursos_outros,
        capital_recursos_total=dados.capital_recursos_total,
        composicao_nacional_pct=dados.composicao_nacional_pct,
        composicao_estrangeiro_pct=dados.composicao_estrangeiro_pct,
        principais_acionistas=dados.principais_acionistas,
        projeto_objetivo=dados.projeto_objetivo,
        distrito_industrial=dados.distrito_industrial,
        area_terreno_m2=dados.area_terreno_m2,
        prazo_implantacao_inicio=dados.prazo_implantacao_inicio,
        prazo_implantacao_termino=dados.prazo_implantacao_termino,
        prazo_expansao_inicio=dados.prazo_expansao_inicio,
        prazo_expansao_termino=dados.prazo_expansao_termino,
        eng_area_construida_implantacao=dados.eng_area_construida_implantacao,
        eng_area_construida_expansao=dados.eng_area_construida_expansao,
        eng_area_estocagem_implantacao=dados.eng_area_estocagem_implantacao,
        eng_area_estocagem_expansao=dados.eng_area_estocagem_expansao,
        eng_estacionamento_implantacao=dados.eng_estacionamento_implantacao,
        eng_estacionamento_expansao=dados.eng_estacionamento_expansao,
        fluxo_producao_descricao=dados.fluxo_producao_descricao,
        saneamento_consumo_agua=dados.saneamento_consumo_agua,
        saneamento_geracao_esgoto=dados.saneamento_geracao_esgoto,
        saneamento_volume_rejeitos=dados.saneamento_volume_rejeitos,
        saneamento_estado_fisico_rejeitos=dados.saneamento_estado_fisico_rejeitos,
        saneamento_tratamento_proprio=dados.saneamento_tratamento_proprio,
        saneamento_equipamento_controle=dados.saneamento_equipamento_controle,
        saneamento_consumo_energia=dados.saneamento_consumo_energia,
        saneamento_potencia_instalada=dados.saneamento_potencia_instalada,
        empregos_diretos=dados.empregos_diretos,
        empregos_indiretos=dados.empregos_indiretos,
        mao_obra_local_pct=dados.mao_obra_local_pct,
        responsavel_tecnico_nome=dados.responsavel_tecnico_nome,
        responsavel_tecnico_registro=dados.responsavel_tecnico_registro,
    )

    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{protocolo}_anexo_vi_evtf.pdf"
    caminho_completo = os.path.join(settings.upload_dir, nome_arquivo)

    HTML(string=html_renderizado).write_pdf(caminho_completo)

    return caminho_completo
