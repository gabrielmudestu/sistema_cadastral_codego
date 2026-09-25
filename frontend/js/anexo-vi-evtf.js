const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';

const form = document.getElementById('form-anexo-vi-evtf');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');

function onlyDigits(value) {
  return value.replace(/\D/g, '');
}

function maskCnpj(digits) {
  return digits
    .slice(0, 14)
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
}

function maskCpf(digits) {
  return digits
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

function maskTelefone(digits) {
  const d = digits.slice(0, 11);
  if (d.length <= 10) {
    return d
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d{1,4})$/, '$1-$2');
  }
  return d
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d{1,4})$/, '$1-$2');
}

document.getElementById('cnpj').addEventListener('input', (e) => {
  e.target.value = maskCnpj(onlyDigits(e.target.value));
});
document.getElementById('responsavel_cpf').addEventListener('input', (e) => {
  e.target.value = maskCpf(onlyDigits(e.target.value));
});
document.getElementById('telefone').addEventListener('input', (e) => {
  e.target.value = maskTelefone(onlyDigits(e.target.value));
});
document.getElementById('uf').addEventListener('input', (e) => {
  e.target.value = e.target.value.toUpperCase().slice(0, 2);
});

function maskCep(digits) {
  return digits.slice(0, 8).replace(/(\d{5})(\d{1,3})$/, '$1-$2');
}

document.getElementById('cep').addEventListener('input', (e) => {
  e.target.value = maskCep(onlyDigits(e.target.value));
});
document.getElementById('responsavel_cep').addEventListener('input', (e) => {
  e.target.value = maskCep(onlyDigits(e.target.value));
});

const cepInput = document.getElementById('cep_busca');
const cepStatusEl = document.getElementById('cep_busca-status');
const enderecoInput = document.getElementById('endereco');
const cidadeInput = document.getElementById('cidade');
const ufInput = document.getElementById('uf');
const cepPrincipalInput = document.getElementById('cep');

cepInput.addEventListener('input', (e) => {
  e.target.value = maskCep(onlyDigits(e.target.value));
  cepStatusEl.textContent = '';
  cepStatusEl.className = 'field__hint';
});

cepInput.addEventListener('blur', async () => {
  const cepDigits = onlyDigits(cepInput.value);
  if (cepDigits.length !== 8) return;

  cepStatusEl.textContent = 'Buscando endereço...';
  cepStatusEl.className = 'field__hint';

  try {
    const response = await fetch(`https://viacep.com.br/ws/${cepDigits}/json/`);
    const dados = await response.json();

    if (dados.erro) {
      cepStatusEl.textContent = 'CEP não encontrado. Preencha o endereço manualmente.';
      cepStatusEl.className = 'field__hint field__hint--warn';
      return;
    }

    const partes = [dados.logradouro, dados.bairro].filter((p) => p && p.trim());
    if (!enderecoInput.value.trim()) enderecoInput.value = partes.join(', ');
    if (!cidadeInput.value.trim()) cidadeInput.value = dados.localidade || '';
    if (!ufInput.value.trim()) ufInput.value = dados.uf || '';
    if (!cepPrincipalInput.value.trim()) cepPrincipalInput.value = maskCep(cepDigits);

    cepStatusEl.textContent = `Endereço encontrado: ${partes.join(', ')}, ${dados.localidade}-${dados.uf}. Complete com número/complemento, se necessário.`;
    cepStatusEl.className = 'field__hint field__hint--ok';
    clearError('endereco');
  } catch (error) {
    cepStatusEl.textContent = 'Não foi possível consultar o CEP agora. Preencha o endereço manualmente.';
    cepStatusEl.className = 'field__hint field__hint--warn';
  }
});

function setError(fieldName, message) {
  const errorEl = document.querySelector(`[data-error-for="${fieldName}"]`);
  if (!errorEl) return;
  const field = document.getElementById(fieldName);
  if (field) field.closest('.field')?.classList.add('field--invalid');
  errorEl.textContent = message;
}

function clearError(fieldName) {
  const errorEl = document.querySelector(`[data-error-for="${fieldName}"]`);
  if (!errorEl) return;
  const field = document.getElementById(fieldName);
  if (field) field.closest('.field')?.classList.remove('field--invalid');
  errorEl.textContent = '';
}

function validateEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

const CAMPOS_TEXTO_OBRIGATORIOS = [
  ['razao_social', 'Informe a razão social.'],
  ['endereco', 'Informe o endereço.'],
  ['cidade', 'Informe a cidade.'],
  ['uf', 'Informe a UF.'],
  ['cep', 'Informe o CEP.'],
  ['responsavel_nome', 'Informe o nome do responsável.'],
  ['responsavel_ci_orgao', 'Informe a CI e o órgão expedidor.'],
  ['responsavel_endereco', 'Informe o endereço do responsável.'],
  ['responsavel_cidade_uf', 'Informe a cidade/UF do responsável.'],
  ['responsavel_cep', 'Informe o CEP do responsável.'],
  ['responsavel_cargo', 'Informe o cargo/função.'],
  ['responsavel_contato', 'Informe o contato.'],
  ['ramo_atividade_cnae', 'Informe o código CNAE.'],
  ['ramo_atividade_especificacao', 'Informe a especificação do ramo de atividade.'],
  ['projeto_objetivo', 'Descreva o objetivo do projeto.'],
  ['distrito_industrial', 'Informe o distrito industrial.'],
  ['area_terreno_m2', 'Informe a área do terreno.'],
  ['fluxo_producao_descricao', 'Descreva o fluxo de produção.'],
  ['empregos_diretos', 'Informe o número de empregos diretos.'],
  ['empregos_indiretos', 'Informe o número de empregos indiretos.'],
  ['responsavel_tecnico_nome', 'Informe o nome do responsável técnico.'],
  ['responsavel_tecnico_registro', 'Informe o número de registro do responsável técnico.'],
];

function validateForm() {
  let valid = true;

  for (const [id, mensagem] of CAMPOS_TEXTO_OBRIGATORIOS) {
    const el = document.getElementById(id);
    if (!el.value.trim()) {
      setError(id, mensagem);
      valid = false;
    } else {
      clearError(id);
    }
  }

  const cnpjDigits = onlyDigits(document.getElementById('cnpj').value);
  if (cnpjDigits.length !== 14) {
    setError('cnpj', 'CNPJ deve ter 14 dígitos.');
    valid = false;
  } else {
    clearError('cnpj');
  }

  const cpfDigits = onlyDigits(document.getElementById('responsavel_cpf').value);
  if (cpfDigits.length !== 11) {
    setError('responsavel_cpf', 'CPF deve ter 11 dígitos.');
    valid = false;
  } else {
    clearError('responsavel_cpf');
  }

  const telDigits = onlyDigits(document.getElementById('telefone').value);
  if (telDigits.length < 10) {
    setError('telefone', 'Informe um telefone válido, com DDD.');
    valid = false;
  } else {
    clearError('telefone');
  }

  const emailValue = document.getElementById('email').value.trim();
  if (!validateEmail(emailValue)) {
    setError('email', 'Informe um e-mail válido.');
    valid = false;
  } else {
    clearError('email');
  }

  const respEmailValue = document.getElementById('responsavel_email').value.trim();
  if (!validateEmail(respEmailValue)) {
    setError('responsavel_email', 'Informe um e-mail válido.');
    valid = false;
  } else {
    clearError('responsavel_email');
  }

  if (typeof grecaptcha !== 'undefined' && !grecaptcha.getResponse()) {
    setError('recaptcha', 'Confirme que você não é um robô.');
    valid = false;
  } else {
    clearError('recaptcha');
  }

  return valid;
}

function showFeedback(html, type) {
  feedbackEl.innerHTML = html;
  feedbackEl.className = `feedback feedback--${type}`;
  feedbackEl.hidden = false;
  feedbackEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideFeedback() {
  feedbackEl.hidden = true;
  feedbackEl.innerHTML = '';
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? 'Gerando documento…' : 'Gerar documento PDF';
}

function extrairMensagemErro(payload) {
  if (!payload) return 'Não foi possível processar o cadastro. Tente novamente.';
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((erro) => erro.msg || 'Campo inválido.').join(' ');
  }
  return 'Não foi possível processar o cadastro. Tente novamente.';
}

function valorOuNulo(id) {
  const valor = document.getElementById(id).value.trim();
  return valor || null;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideFeedback();

  if (!validateForm()) return;

  const payload = {
    razao_social: document.getElementById('razao_social').value.trim(),
    cnpj: document.getElementById('cnpj').value,
    endereco: document.getElementById('endereco').value.trim(),
    cidade: document.getElementById('cidade').value.trim(),
    uf: document.getElementById('uf').value.trim(),
    cep: document.getElementById('cep').value,
    telefone: document.getElementById('telefone').value,
    email: document.getElementById('email').value.trim(),
    conta_corrente: valorOuNulo('conta_corrente'),
    banco: valorOuNulo('banco'),
    agencia: valorOuNulo('agencia'),
    praca_pagamento: valorOuNulo('praca_pagamento'),
    responsavel_nome: document.getElementById('responsavel_nome').value.trim(),
    responsavel_ci_orgao: document.getElementById('responsavel_ci_orgao').value.trim(),
    responsavel_cpf: document.getElementById('responsavel_cpf').value,
    responsavel_endereco: document.getElementById('responsavel_endereco').value.trim(),
    responsavel_cidade_uf: document.getElementById('responsavel_cidade_uf').value.trim(),
    responsavel_cep: document.getElementById('responsavel_cep').value,
    responsavel_cargo: document.getElementById('responsavel_cargo').value.trim(),
    responsavel_contato: document.getElementById('responsavel_contato').value.trim(),
    responsavel_email: document.getElementById('responsavel_email').value.trim(),
    ramo_atividade_cnae: document.getElementById('ramo_atividade_cnae').value.trim(),
    ramo_atividade_especificacao: document.getElementById('ramo_atividade_especificacao').value.trim(),
    capital_social_data: valorOuNulo('capital_social_data'),
    capital_social_ato: valorOuNulo('capital_social_ato'),
    capital_recursos_proprios: valorOuNulo('capital_recursos_proprios'),
    capital_recursos_incentivos: valorOuNulo('capital_recursos_incentivos'),
    capital_recursos_outros: valorOuNulo('capital_recursos_outros'),
    capital_recursos_total: valorOuNulo('capital_recursos_total'),
    composicao_nacional_pct: valorOuNulo('composicao_nacional_pct'),
    composicao_estrangeiro_pct: valorOuNulo('composicao_estrangeiro_pct'),
    principais_acionistas: valorOuNulo('principais_acionistas'),
    projeto_objetivo: document.getElementById('projeto_objetivo').value.trim(),
    distrito_industrial: document.getElementById('distrito_industrial').value.trim(),
    area_terreno_m2: document.getElementById('area_terreno_m2').value.trim(),
    prazo_implantacao_inicio: valorOuNulo('prazo_implantacao_inicio'),
    prazo_implantacao_termino: valorOuNulo('prazo_implantacao_termino'),
    prazo_expansao_inicio: valorOuNulo('prazo_expansao_inicio'),
    prazo_expansao_termino: valorOuNulo('prazo_expansao_termino'),
    eng_area_construida_implantacao: valorOuNulo('eng_area_construida_implantacao'),
    eng_area_construida_expansao: valorOuNulo('eng_area_construida_expansao'),
    eng_area_estocagem_implantacao: valorOuNulo('eng_area_estocagem_implantacao'),
    eng_area_estocagem_expansao: valorOuNulo('eng_area_estocagem_expansao'),
    eng_estacionamento_implantacao: valorOuNulo('eng_estacionamento_implantacao'),
    eng_estacionamento_expansao: valorOuNulo('eng_estacionamento_expansao'),
    fluxo_producao_descricao: document.getElementById('fluxo_producao_descricao').value.trim(),
    saneamento_consumo_agua: valorOuNulo('saneamento_consumo_agua'),
    saneamento_geracao_esgoto: valorOuNulo('saneamento_geracao_esgoto'),
    saneamento_volume_rejeitos: valorOuNulo('saneamento_volume_rejeitos'),
    saneamento_estado_fisico_rejeitos: valorOuNulo('saneamento_estado_fisico_rejeitos'),
    saneamento_tratamento_proprio: valorOuNulo('saneamento_tratamento_proprio'),
    saneamento_equipamento_controle: valorOuNulo('saneamento_equipamento_controle'),
    saneamento_consumo_energia: valorOuNulo('saneamento_consumo_energia'),
    saneamento_potencia_instalada: valorOuNulo('saneamento_potencia_instalada'),
    empregos_diretos: document.getElementById('empregos_diretos').value.trim(),
    empregos_indiretos: document.getElementById('empregos_indiretos').value.trim(),
    mao_obra_local_pct: valorOuNulo('mao_obra_local_pct'),
    responsavel_tecnico_nome: document.getElementById('responsavel_tecnico_nome').value.trim(),
    responsavel_tecnico_registro: document.getElementById('responsavel_tecnico_registro').value.trim(),
    g_recaptcha_response: typeof grecaptcha !== 'undefined' ? grecaptcha.getResponse() : '',
  };

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/anexo-vi-evtf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      showFeedback(
        `<p class="feedback__title">Não foi possível gerar o documento</p><p>${extrairMensagemErro(data)}</p>`,
        'error'
      );
      return;
    }

    const protocolo = data.processo.protocolo;
    const pdfUrl = `${API_BASE_URL}${data.pdf_download_url}`;

    showFeedback(
      `<p class="feedback__title">Documento gerado com sucesso</p>
       <p>Baixe o PDF, assine (digitalmente ou impresso) e prossiga para a etapa de reenvio do documento assinado.</p>
       <p class="feedback__protocolo">Protocolo: ${protocolo}</p>
       ${data.email_protocolo_enviado
         ? '<p class="feedback__email-status feedback__email-status--ok">✓ Enviamos o protocolo e o documento para o e-mail informado.</p>'
         : '<p class="feedback__email-status feedback__email-status--warn">Não foi possível enviar o protocolo por e-mail. Anote o número acima: ele é necessário para enviar o documento assinado.</p>'}
       <div class="feedback__actions">
         <a class="feedback__link" href="${pdfUrl}" target="_blank" rel="noopener">Baixar documento PDF</a>
         <a class="feedback__link feedback__link--secondary" href="upload-assinado.html?protocolo=${encodeURIComponent(protocolo)}">Já assinei, enviar documento →</a>
       </div>`,
      'success'
    );

    form.reset();
  } catch (error) {
    showFeedback(
      `<p class="feedback__title">Falha de conexão</p><p>Não foi possível falar com o servidor. Verifique se a API está em execução e tente novamente.</p>`,
      'error'
    );
  } finally {
    setLoading(false);
    if (typeof grecaptcha !== 'undefined') {
      grecaptcha.reset();
    }
  }
});
