import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Usuario, ProcessoDocumento, StatusProcesso, TipoDocumento
from app.schemas.cadastro import CadastroResponse
from app.schemas.anexo_viii_d import AnexoViiiDCreate
from app.schemas.anexo_viii_a import AnexoViiiACreate
from app.schemas.anexo_iii import AnexoIiiCreate
from app.schemas.anexo_v_declaracao_uso import AnexoVDeclaracaoUsoCreate
from app.schemas.anexo_v_cfo import AnexoVCfoCreate
from app.schemas.anexo_vii_mce import AnexoViiMceCreate
from app.schemas.anexo_viii_b import AnexoViiiBCreate
from app.schemas.anexo_viii_c import AnexoViiiCCreate
from app.schemas.anexo_ix import AnexoIXCreate
from app.schemas.anexo_vi_evtf import AnexoVIEvtfCreate
from app.services.protocolo import gerar_protocolo
from app.services.pdf_generator import (
    gerar_pdf_anexo_viii_d,
    gerar_pdf_anexo_viii_a,
    gerar_pdf_anexo_iii,
    gerar_pdf_anexo_v_declaracao_uso,
    gerar_pdf_anexo_v_cfo,
    gerar_pdf_anexo_vii_mce,
    gerar_pdf_anexo_viii_b,
    gerar_pdf_anexo_viii_c,
    gerar_pdf_anexo_ix,
    gerar_pdf_anexo_vi_evtf,
)
from app.services.email_service import enviar_email_protocolo
from app.services.recaptcha import verificar_recaptcha

router = APIRouter()


def _enviar_protocolo(email: str | None, nome_empresarial: str, nome_documento: str, protocolo: str, caminho_pdf: str) -> bool:
    """
    Envia o protocolo (com o PDF gerado em anexo) para o e-mail informado no
    formulário. Falha de e-mail não impede a geração do documento: só é
    registrada no log e informada na resposta.
    """
    if not email:
        return False
    enviado, _erro = enviar_email_protocolo(email, nome_empresarial, nome_documento, protocolo, caminho_pdf)
    return enviado


@router.post("/anexo-viii-d", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_viii_d(payload: AnexoViiiDCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VIII-D com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Etapa 1 do fluxo).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_viii_d(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VIII_D,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo VIII-D — Solicitações Diversas", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-viii-a", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_viii_a(payload: AnexoViiiACreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VIII-A com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Pedido de Anuência para Alienação entre Particulares).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_viii_a(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VIII_A,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo VIII-A — Alienação entre Particulares", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-iii", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_iii(payload: AnexoIiiCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo III com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Solicitação de Área).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefones[:30],
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_iii(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_III,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo III — Solicitação de Área", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-v-declaracao-uso", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_v_declaracao_uso(payload: AnexoVDeclaracaoUsoCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo V com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Declaração de Uso da Rede de Abastecimento de Água e de Esgoto da CODEGO).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_v_declaracao_uso(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_V_DECLARACAO_USO,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo V — Declaração de Uso de Água e Esgoto", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-v-cfo", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_v_cfo(payload: AnexoVCfoCreate, db: Session = Depends(get_db)):
    """
    Abre um novo processo do tipo Anexo V (Cronograma Físico da Obra — CFO) com
    protocolo único, e gera o PDF preenchido no modelo oficial do documento.
    O modelo do CFO não pede CNPJ nem e-mail, então o processo não é vinculado
    a um cadastro de usuário/empresa.
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_v_cfo(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=None,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_V_CFO,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    return CadastroResponse(
        usuario=None,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
    )


@router.post("/anexo-vii-mce", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_vii_mce(payload: AnexoViiMceCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VII com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Memorial de Caracterização do Empreendimento — MCE).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.razao_social,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo=payload.responsavel_cargo,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_vii_mce(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VII_MCE,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.razao_social, "Anexo VII — Memorial de Caracterização do Empreendimento", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-viii-b", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_viii_b(payload: AnexoViiiBCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VIII-B com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Pedido de Anuência para Remembramento/Desmembramento
    de Área).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_viii_b(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VIII_B,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo VIII-B — Remembramento/Desmembramento", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-viii-c", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_viii_c(payload: AnexoViiiCCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VIII-C com protocolo único, e gera o PDF preenchido no modelo
    oficial do documento (Pedido de Anuência para Fusão, Cisão, Incorporação,
    Mudança do Quadro Societário, Mudança da Atividade Econômica e demais
    alterações do Contrato Social).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo="Representante legal",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_viii_c(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VIII_C,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo VIII-C — Alterações do Contrato Social", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-ix", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_ix(payload: AnexoIXCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo IX com protocolo único, e gera o PDF preenchido no modelo oficial
    do documento (Formulário de Atualização Cadastral Anual).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.nome_empresarial,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo=payload.responsavel,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_ix(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_IX,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.nome_empresarial, "Anexo IX — Atualização Cadastral Anual", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.post("/anexo-vi-evtf", response_model=CadastroResponse, status_code=201)
def criar_cadastro_anexo_vi_evtf(payload: AnexoVIEvtfCreate, db: Session = Depends(get_db)):
    """
    Cria (ou reaproveita) o usuário/empresa pelo CNPJ, abre um novo processo do
    tipo Anexo VI com protocolo único, e gera o PDF preenchido no modelo oficial
    do documento (Formulário de Viabilidade Técnica e Financeira - EVTF).
    """
    recaptcha_ok, recaptcha_erro = verificar_recaptcha(payload.g_recaptcha_response)
    if not recaptcha_ok:
        raise HTTPException(status_code=422, detail=recaptcha_erro)

    usuario = db.query(Usuario).filter(Usuario.cpf_cnpj == payload.cnpj).first()
    if usuario is None:
        usuario = Usuario(
            nome=payload.razao_social,
            cpf_cnpj=payload.cnpj,
            email=payload.email,
            telefone=payload.telefone,
            cargo=payload.responsavel_cargo,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    protocolo = gerar_protocolo()
    while db.query(ProcessoDocumento).filter(ProcessoDocumento.protocolo == protocolo).first():
        protocolo = gerar_protocolo()

    caminho_pdf = gerar_pdf_anexo_vi_evtf(payload, protocolo)

    processo = ProcessoDocumento(
        usuario_id=usuario.id,
        protocolo=protocolo,
        tipo_documento=TipoDocumento.ANEXO_VI_EVTF,
        dados_formulario=json.loads(payload.model_dump_json()),
        caminho_pdf_preenchido=caminho_pdf,
        status=StatusProcesso.PENDENTE,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    email_enviado = _enviar_protocolo(
        payload.email, payload.razao_social, "Anexo VI — Viabilidade Técnica e Financeira (EVTF)", protocolo, caminho_pdf
    )

    return CadastroResponse(
        usuario=usuario,
        processo=processo,
        pdf_download_url=f"/api/cadastro/{processo.id}/pdf",
        email_protocolo_enviado=email_enviado,
    )


@router.get("/{processo_id}")
def obter_cadastro(processo_id: int, db: Session = Depends(get_db)):
    processo = db.query(ProcessoDocumento).filter(ProcessoDocumento.id == processo_id).first()
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    return processo
