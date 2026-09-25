from app.models.orm import ProcessoDocumento, TipoDocumento
from app.schemas.anexo_iii import DOCUMENTOS_ANEXO_III


def documentos_exigidos(processo: ProcessoDocumento) -> list[dict[str, str]]:
    """
    Documentos que a pessoa marcou no formulário como anexos do requerimento
    e que devem ser enviados junto com o documento assinado. Hoje só o
    Anexo III tem essa lista; os demais anexos não exigem documentos.
    """
    if TipoDocumento(processo.tipo_documento) != TipoDocumento.ANEXO_III:
        return []

    marcados = set((processo.dados_formulario or {}).get("documentos") or [])
    return [
        {"codigo": codigo, "descricao": " ".join(descricao.split())}
        for codigo, descricao in DOCUMENTOS_ANEXO_III.items()
        if codigo in marcados
    ]
