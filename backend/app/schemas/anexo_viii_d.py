from pydantic import BaseModel, EmailStr, field_validator, model_validator

# Chaves e rótulos das solicitações do Anexo VIII-D, na ordem em que aparecem no
# documento original. A chave é o que o front-end envia; o rótulo é o texto exato
# usado no PDF.
SOLICITACOES_ANEXO_VIII_D: dict[str, str] = {
    "juntada_documentacao": "Juntada de documentação ao processo administrativo",
    "declaracao_existencia": "Declaração de existência de processo junto à Companhia",
    "declaracao_regularidade": "Declaração de regularidade junto à Companhia",
    "declaracao_assentamento": "Declaração de assentamento da empresa no endereço supracitado",
    "reuniao_tratativas": (
        "Realização de reunião para tratativas sobre acordo em processo judicial "
        "(deverá ser acompanhado de procuração com poderes específicos)"
    ),
    "copia_processo": "Cópia do processo administrativo",
    "outros": "Outros",
}

ESTADOS_CIVIS_VALIDOS = {
    "Solteiro(a)",
    "Casado(a)",
    "Divorciado(a)",
    "Viúvo(a)",
    "União estável",
}


class AnexoViiiDCreate(BaseModel):
    # Dados da empresa (tabela do formulário)
    processo_numero: str
    nome_empresarial: str
    cnpj: str
    endereco: str
    telefone: str
    email: EmailStr

    # Representante legal (parágrafo de qualificação)
    representante_nome: str
    representante_estado_civil: str
    representante_rg: str
    representante_cpf: str
    representante_endereco: str

    # Solicitações e motivação
    solicitacoes: list[str]
    outros_texto: str | None = None
    motivacao: str

    @field_validator(
        "processo_numero",
        "nome_empresarial",
        "endereco",
        "telefone",
        "representante_nome",
        "representante_estado_civil",
        "representante_rg",
        "representante_endereco",
        "motivacao",
    )
    @classmethod
    def campo_nao_vazio(cls, v: str, info):
        if not v or not v.strip():
            raise ValueError(f"O campo '{info.field_name}' é obrigatório.")
        return v.strip()

    @field_validator("cnpj")
    @classmethod
    def valida_cnpj(cls, v: str):
        digits = "".join(filter(str.isdigit, v))
        if len(digits) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos.")
        return digits

    @field_validator("representante_cpf")
    @classmethod
    def valida_cpf_representante(cls, v: str):
        digits = "".join(filter(str.isdigit, v))
        if len(digits) != 11:
            raise ValueError("CPF do representante deve ter 11 dígitos.")
        return digits

    @field_validator("telefone")
    @classmethod
    def valida_telefone(cls, v: str):
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Telefone deve ter DDD + número (mínimo 10 dígitos).")
        return digits

    @field_validator("representante_estado_civil")
    @classmethod
    def valida_estado_civil(cls, v: str):
        if v not in ESTADOS_CIVIS_VALIDOS:
            raise ValueError(f"Estado civil inválido. Opções: {', '.join(sorted(ESTADOS_CIVIS_VALIDOS))}")
        return v

    @field_validator("solicitacoes")
    @classmethod
    def valida_solicitacoes(cls, v: list[str]):
        if not v:
            raise ValueError("Selecione ao menos uma solicitação.")
        invalidas = set(v) - set(SOLICITACOES_ANEXO_VIII_D.keys())
        if invalidas:
            raise ValueError(f"Solicitações inválidas: {', '.join(invalidas)}")
        return v

    @model_validator(mode="after")
    def valida_outros_texto(self):
        if "outros" in self.solicitacoes and not (self.outros_texto or "").strip():
            raise ValueError("Descreva o campo 'Outros' quando essa opção estiver marcada.")
        return self
