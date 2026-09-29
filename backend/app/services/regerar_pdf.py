import logging

from app.models.orm import ProcessoDocumento, TipoDocumento
from app.schemas.anexo_iii import AnexoIiiCreate
from app.schemas.anexo_ix import AnexoIXCreate
from app.schemas.anexo_v_cfo import AnexoVCfoCreate
from app.schemas.anexo_v_declaracao_uso import AnexoVDeclaracaoUsoCreate
from app.schemas.anexo_vi_evtf import AnexoVIEvtfCreate
from app.schemas.anexo_vii_mce import AnexoViiMceCreate
from app.schemas.anexo_viii_a import AnexoViiiACreate
from app.schemas.anexo_viii_b import AnexoViiiBCreate
from app.schemas.anexo_viii_c import AnexoViiiCCreate
from app.schemas.anexo_viii_d import AnexoViiiDCreate
from app.services import pdf_generator

logger = logging.getLogger("codego.pdf")

GERADORES = {
    TipoDocumento.ANEXO_VIII_D: (AnexoViiiDCreate, pdf_generator.gerar_pdf_anexo_viii_d),
    TipoDocumento.ANEXO_VIII_A: (AnexoViiiACreate, pdf_generator.gerar_pdf_anexo_viii_a),
    TipoDocumento.ANEXO_VIII_B: (AnexoViiiBCreate, pdf_generator.gerar_pdf_anexo_viii_b),
    TipoDocumento.ANEXO_VIII_C: (AnexoViiiCCreate, pdf_generator.gerar_pdf_anexo_viii_c),
    TipoDocumento.ANEXO_III: (AnexoIiiCreate, pdf_generator.gerar_pdf_anexo_iii),
    TipoDocumento.ANEXO_V_DECLARACAO_USO: (AnexoVDeclaracaoUsoCreate, pdf_generator.gerar_pdf_anexo_v_declaracao_uso),
    TipoDocumento.ANEXO_V_CFO: (AnexoVCfoCreate, pdf_generator.gerar_pdf_anexo_v_cfo),
    TipoDocumento.ANEXO_VII_MCE: (AnexoViiMceCreate, pdf_generator.gerar_pdf_anexo_vii_mce),
    TipoDocumento.ANEXO_IX: (AnexoIXCreate, pdf_generator.gerar_pdf_anexo_ix),
    TipoDocumento.ANEXO_VI_EVTF: (AnexoVIEvtfCreate, pdf_generator.gerar_pdf_anexo_vi_evtf),
}


def regerar_pdf_preenchido(processo: ProcessoDocumento) -> str | None:
    """
    Recria o PDF preenchido de um processo a partir dos dados salvos no banco,
    com a data original do processo. Usado quando o arquivo não existe mais no
    disco — ex.: no Render grátis, que apaga os arquivos a cada reinício.
    Retorna o caminho do PDF recriado, ou None se não for possível.
    """
    tipo = TipoDocumento(processo.tipo_documento)
    if tipo not in GERADORES or not processo.dados_formulario:
        return None

    schema, gerar = GERADORES[tipo]
    token = pdf_generator.data_do_documento.set(processo.data_geracao)
    try:
        dados = schema.model_validate(processo.dados_formulario, context={"regerar_pdf": True})
        caminho = gerar(dados, processo.protocolo)
    except Exception:  # noqa: BLE001 — sem o PDF, o download responde 404 como antes
        logger.exception("Não foi possível recriar o PDF do processo %s", processo.protocolo)
        return None
    finally:
        pdf_generator.data_do_documento.reset(token)

    logger.info("PDF do processo %s recriado a partir dos dados salvos.", processo.protocolo)
    return caminho
