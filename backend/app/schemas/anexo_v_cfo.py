import re

from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from app.schemas.validacoes import formatar_numero_br, mes_atual, numero_br, regerando_pdf

# Serviços que já aparecem no modelo do cronograma. O front-end usa essa lista
# como sugestão inicial; o usuário pode remover/adicionar serviços livremente.
SERVICOS_SUGERIDOS_CFO = [
    "Serviços preliminares",
    "Infraestrutura",
    "Paredes e Painéis",
    "Cobertura",
    "Pavimentação",
]

MAX_MESES_CFO = 60

_MES_ANO_RE = re.compile(r"^(\d{4})-(\d{2})$")


def _parse_mes_ano(v: str) -> tuple[int, int]:
    match = _MES_ANO_RE.match(v or "")
    if not match:
        raise ValueError("Use o formato AAAA-MM.")
    ano, mes = int(match.group(1)), int(match.group(2))
    if not 1 <= mes <= 12:
        raise ValueError("Mês inválido.")
    return ano, mes


def total_meses(inicio: str, termino: str) -> int:
    """Quantidade de meses do cronograma, contando o mês de início e o de término."""
    ano_i, mes_i = _parse_mes_ano(inicio)
    ano_t, mes_t = _parse_mes_ano(termino)
    return (ano_t - ano_i) * 12 + (mes_t - mes_i) + 1


class ServicoCFO(BaseModel):
    descricao: str
    # Percentual executado em cada mês da obra (mesmo tamanho que a quantidade de
    # meses do cronograma). Mês sem execução = 0.
    percentuais: list[float]

    @field_validator("descricao")
    @classmethod
    def descricao_nao_vazia(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Informe a descrição de cada serviço do cronograma.")
        return v.strip()

    @field_validator("percentuais")
    @classmethod
    def percentuais_validos(cls, v: list[float]):
        if any(p < 0 or p > 100 for p in v):
            raise ValueError("Cada percentual mensal deve estar entre 0% e 100%.")
        return v


class AnexoVCfoCreate(BaseModel):
    # Cabeçalho do cronograma
    nome_empresa: str
    endereco: str
    area_empresa: str
    area_construida: str
    inicio_obras: str  # AAAA-MM
    termino_obras: str  # AAAA-MM

    servicos: list[ServicoCFO]

    g_recaptcha_response: str = ""

    @field_validator("nome_empresa", "endereco", "area_empresa", "area_construida")
    @classmethod
    def campo_nao_vazio(cls, v: str, info):
        if not v or not v.strip():
            raise ValueError(f"O campo '{info.field_name}' é obrigatório.")
        return v.strip()

    @field_validator("area_empresa", "area_construida")
    @classmethod
    def valida_area(cls, v: str, info):
        rotulo = "Área da Empresa" if info.field_name == "area_empresa" else "Área a ser Construída"
        try:
            valor = numero_br(v)
        except ValueError as exc:
            raise ValueError(f"{rotulo}: {exc}") from exc
        if valor <= 0:
            raise ValueError(f"{rotulo} deve ser maior que zero.")
        return formatar_numero_br(valor)

    @model_validator(mode="after")
    def valida_areas_coerentes(self):
        if numero_br(self.area_construida) > numero_br(self.area_empresa):
            raise ValueError("A área a ser construída não pode ser maior que a área da empresa.")
        return self

    @field_validator("inicio_obras", "termino_obras")
    @classmethod
    def valida_mes_ano(cls, v: str, info):
        try:
            _parse_mes_ano(v)
        except ValueError as exc:
            raise ValueError(f"Campo '{info.field_name}': {exc}") from exc
        return v

    @field_validator("servicos")
    @classmethod
    def valida_servicos(cls, v: list[ServicoCFO]):
        if not v:
            raise ValueError("Informe ao menos um serviço no cronograma.")
        return v

    @model_validator(mode="after")
    def valida_cronograma(self, info: ValidationInfo):
        if self.inicio_obras < mes_atual() and not regerando_pdf(info):
            raise ValueError("A previsão de início das obras não pode ser um mês que já passou.")
        meses = total_meses(self.inicio_obras, self.termino_obras)
        if meses < 1:
            raise ValueError("A previsão de término das obras deve ser igual ou posterior ao início.")
        if meses > MAX_MESES_CFO:
            raise ValueError(f"O cronograma pode ter no máximo {MAX_MESES_CFO} meses.")

        for servico in self.servicos:
            if len(servico.percentuais) != meses:
                raise ValueError(
                    f"O serviço '{servico.descricao}' deve ter um percentual para cada um dos {meses} meses."
                )
            # Cada serviço precisa fechar 100% ao longo da obra (ex.: 50% + 50%,
            # 25% x 4, como no modelo). Tolerância para arredondamentos.
            if abs(sum(servico.percentuais) - 100) > 0.01:
                raise ValueError(
                    f"Os percentuais do serviço '{servico.descricao}' devem somar 100% "
                    f"(atualmente somam {sum(servico.percentuais):g}%)."
                )
        return self
