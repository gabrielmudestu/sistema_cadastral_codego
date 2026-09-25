const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';

const form = document.getElementById('form-anexo-ix');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');

function onlyDigits(value) {
  return value.replace(/\D/g, '');
}

// Confere os dígitos verificadores (mesma regra do servidor).
function cpfValido(digits) {
  if (digits.length !== 11 || /^(\d)\1+$/.test(digits)) return false;
  for (const tamanho of [9, 10]) {
    let soma = 0;
    for (let i = 0; i < tamanho; i += 1) soma += Number(digits[i]) * (tamanho + 1 - i);
    if (((soma * 10) % 11) % 10 !== Number(digits[tamanho])) return false;
  }
  return true;
}

function cnpjValido(digits) {
  if (digits.length !== 14 || /^(\d)\1+$/.test(digits)) return false;
  const pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  for (const tamanho of [12, 13]) {
    const p = tamanho === 12 ? pesos : [6, ...pesos];
    let soma = 0;
    for (let i = 0; i < tamanho; i += 1) soma += Number(digits[i]) * p[i];
    const resto = soma % 11;
    if ((resto < 2 ? 0 : 11 - resto) !== Number(digits[tamanho])) return false;
  }
  return true;
}

function maskCnpj(digits) {
  return digits
    .slice(0, 14)
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
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
document.getElementById('telefone').addEventListener('input', (e) => {
  e.target.value = maskTelefone(onlyDigits(e.target.value));
});

function maskCep(digits) {
  return digits.slice(0, 8).replace(/(\d{5})(\d{1,3})$/, '$1-$2');
}

const cepInput = document.getElementById('cep_busca');
const cepStatusEl = document.getElementById('cep_busca-status');
const enderecoInput = document.getElementById('endereco');

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

    const partes = [dados.logradouro, dados.bairro, `${dados.localidade}-${dados.uf}`]
      .filter((parte) => parte && parte.trim());
    const enderecoEncontrado = partes.join(', ');

    if (!enderecoInput.value.trim()) {
      enderecoInput.value = enderecoEncontrado;
    }

    cepStatusEl.textContent = `Endereço encontrado: ${enderecoEncontrado}. Complete com número/complemento, se necessário.`;
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

// ---------------------------------------------------------------------------
// Restrições de digitação: o campo não aceita o que não pode (letra em campo
// de número, valor acima do limite etc.). O que não dá para barrar enquanto a
// pessoa digita (campo vazio ou incompleto) é avisado ao clicar em "Gerar
// documento PDF", rolando a página até o campo.
// ---------------------------------------------------------------------------

// Aplica "formatar" a cada alteração e só aceita o novo valor se "permitido"
// concordar; senão o campo volta ao valor anterior.
function restringirCampo(el, formatar, permitido = () => true) {
  if (!el) return;
  let anterior = el.value;
  el.addEventListener('focus', () => { anterior = el.value; });
  el.addEventListener('input', () => {
    const novo = formatar ? formatar(el.value) : el.value;
    if (!permitido(novo)) {
      el.value = anterior;
      return;
    }
    el.value = novo;
    anterior = novo;
  });
}

// Rola até o primeiro campo com erro e coloca o cursor nele.
function irParaPrimeiroErro() {
  const erro = document.querySelector('.field__error:not(:empty)');
  if (!erro) return;
  const campo = document.getElementById(erro.dataset.errorFor);
  (campo || erro).scrollIntoView({ behavior: 'smooth', block: 'center' });
  if (campo && typeof campo.focus === 'function') campo.focus({ preventScroll: true });
}

// Quando a pessoa começa a corrigir um campo, o aviso dele some.
form.addEventListener('input', (e) => { if (e.target.id) clearError(e.target.id); });
form.addEventListener('change', (e) => { if (e.target.id) clearError(e.target.id); });

// Nome de pessoa: só letras, espaço, apóstrofo, ponto e hífen.
const formatarNomePessoa = (v) => v.replace(/[^\p{L}\s'.-]/gu, '').replace(/\s{2,}/g, ' ');

function validateEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

// --- Campos condicionais: mostra/esconde conforme a seleção ---

function configurarCondicional(gatilhoId, mapa) {
  // mapa: { 'valor selecionado': ['id-do-wrapper-1', 'id-do-wrapper-2'] }
  const gatilho = document.getElementById(gatilhoId);
  const todosWrappers = new Set(Object.values(mapa).flat());

  gatilho.addEventListener('change', () => {
    const wrappersParaMostrar = new Set(mapa[gatilho.value] || []);
    todosWrappers.forEach((wrapperId) => {
      const wrapper = document.getElementById(wrapperId);
      if (!wrapper) return;
      const mostrar = wrappersParaMostrar.has(wrapperId);
      wrapper.hidden = !mostrar;
      if (!mostrar) {
        wrapper.querySelectorAll('input, select').forEach((el) => (el.value = ''));
      }
    });
  });
}

configurarCondicional('status_operacao', {
  'Em recesso': ['status_operacao_prazo_dias-wrapper'],
  'Paralisada': ['status_operacao_paralisada_mes-wrapper'],
  'Outro': ['status_operacao_outro_texto-wrapper'],
});

configurarCondicional('possui_hidrometro', {
  'Sim': ['hidrometro-detalhes'],
});

configurarCondicional('possui_poco_artesiano', {
  'Sim': ['poco_possui_outorga-wrapper'],
});

configurarCondicional('poco_possui_outorga', {
  'Sim': ['outorga-detalhes'],
});

configurarCondicional('responsavel_abastecimento', {
  'Município': ['responsavel_abastecimento_municipio-wrapper'],
});

configurarCondicional('possui_ete', {
  'Sim': ['ete_ativa-wrapper'],
});

configurarCondicional('possui_medidor_vazao', {
  'Outro': ['medidor_vazao_outro_texto-wrapper'],
});

configurarCondicional('responsavel_esgoto', {
  'Outro': ['responsavel_esgoto_outro_texto-wrapper'],
});

const CAMPOS_LICENCA = [
  'licenca_previa',
  'licenca_instalacao',
  'licenca_operacao',
  'licenciamento_bombeiros',
  'certidao_uso_solo',
  'alvara_sanitario',
];
CAMPOS_LICENCA.forEach((campo) => {
  configurarCondicional(campo, { 'Sim': [`${campo}_vigencia-wrapper`] });
});

// --- Validação ---

const CAMPOS_TEXTO_OBRIGATORIOS = [
  ['tecnico_responsavel', 'Informe o técnico responsável.'],
  ['nome_empresarial', 'Informe o nome empresarial.'],
  ['endereco', 'Informe o endereço.'],
  ['distrito', 'Informe o distrito.'],
  ['responsavel', 'Informe o responsável.'],
  ['num_funcionarios', 'Informe o número de funcionários.'],
  ['num_matriculas_imovel', 'Informe o número de matrículas do imóvel.'],
  ['area_total_m2', 'Informe a área total.'],
  ['area_ocupada_m2', 'Informe a área ocupada.'],
  ['taxa_ocupacao', 'Informe a taxa de ocupação.'],
  ['responsavel_tecnico_nome', 'Informe o nome do responsável técnico.'],
  ['responsavel_tecnico_registro', 'Informe o número de registro do responsável técnico.'],
];

const CAMPOS_SELECT_OBRIGATORIOS = [
  ['asfalto_frente', 'Selecione uma opção.'],
  ['status_operacao', 'Selecione o status de operação.'],
  ['possui_hidrometro', 'Selecione uma opção.'],
  ['possui_poco_artesiano', 'Selecione uma opção.'],
  ['responsavel_abastecimento', 'Selecione uma opção.'],
  ['possui_ete', 'Selecione uma opção.'],
  ['possui_medidor_vazao', 'Selecione uma opção.'],
  ['responsavel_esgoto', 'Selecione uma opção.'],
  ...CAMPOS_LICENCA.map((c) => [c, 'Selecione uma opção.']),
];

function validarCondicional(condicaoValor, gatilhoId, campoId, mensagem) {
  const gatilho = document.getElementById(gatilhoId);
  if (gatilho.value !== condicaoValor) {
    clearError(campoId);
    return true;
  }
  const campo = document.getElementById(campoId);
  if (!campo.value.trim()) {
    setError(campoId, mensagem);
    return false;
  }
  clearError(campoId);
  return true;
}

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

  for (const [id, mensagem] of CAMPOS_SELECT_OBRIGATORIOS) {
    const el = document.getElementById(id);
    if (!el.value) {
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
  } else if (!cnpjValido(cnpjDigits)) {
    setError('cnpj', 'CNPJ inválido. Confira os números digitados.');
    valid = false;
  } else {
    clearError('cnpj');
  }

  const telDigits = onlyDigits(document.getElementById('telefone').value);
  if (telDigits.length < 10 || telDigits.length > 11) {
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

  if (!validarCondicional('Em recesso', 'status_operacao', 'status_operacao_prazo_dias', 'Informe o prazo em dias.')) valid = false;
  if (!validarCondicional('Paralisada', 'status_operacao', 'status_operacao_paralisada_mes', 'Informe desde qual mês.')) valid = false;
  if (!validarCondicional('Outro', 'status_operacao', 'status_operacao_outro_texto', 'Descreva o status.')) valid = false;
  if (!validarCondicional('Sim', 'possui_hidrometro', 'hidrometro_quantos', 'Informe quantos hidrômetros.')) valid = false;
  if (!validarCondicional('Sim', 'possui_poco_artesiano', 'poco_possui_outorga', 'Informe se possui outorga.')) valid = false;
  if (!validarCondicional('Sim', 'poco_possui_outorga', 'outorga_vigencia', 'Informe a vigência da outorga.')) valid = false;
  if (!validarCondicional('Município', 'responsavel_abastecimento', 'responsavel_abastecimento_municipio', 'Informe o município.')) valid = false;
  if (!validarCondicional('Sim', 'possui_ete', 'ete_ativa', 'Informe se a ETE está ativa.')) valid = false;
  if (!validarCondicional('Outro', 'possui_medidor_vazao', 'medidor_vazao_outro_texto', 'Descreva o medidor de vazão.')) valid = false;
  if (!validarCondicional('Outro', 'responsavel_esgoto', 'responsavel_esgoto_outro_texto', 'Descreva o responsável.')) valid = false;

  CAMPOS_LICENCA.forEach((campo) => {
    if (!validarCondicional('Sim', campo, `${campo}_vigencia`, 'Informe a vigência.')) valid = false;
  });

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
  const el = document.getElementById(id);
  const valor = el.value.trim();
  return valor || null;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideFeedback();

  if (!validateForm()) {
    irParaPrimeiroErro();
    return;
  }

  const payload = {
    tecnico_responsavel: document.getElementById('tecnico_responsavel').value.trim(),
    nome_empresarial: document.getElementById('nome_empresarial').value.trim(),
    cnpj: document.getElementById('cnpj').value,
    endereco: document.getElementById('endereco').value.trim(),
    distrito: document.getElementById('distrito').value.trim(),
    telefone: document.getElementById('telefone').value,
    email: document.getElementById('email').value.trim(),
    responsavel: document.getElementById('responsavel').value.trim(),
    num_funcionarios: document.getElementById('num_funcionarios').value.trim(),
    num_matriculas_imovel: document.getElementById('num_matriculas_imovel').value.trim(),
    area_total_m2: document.getElementById('area_total_m2').value.trim(),
    area_ocupada_m2: document.getElementById('area_ocupada_m2').value.trim(),
    taxa_ocupacao: document.getElementById('taxa_ocupacao').value.trim(),
    asfalto_frente: document.getElementById('asfalto_frente').value,
    status_operacao: document.getElementById('status_operacao').value,
    status_operacao_prazo_dias: valorOuNulo('status_operacao_prazo_dias'),
    status_operacao_paralisada_mes: valorOuNulo('status_operacao_paralisada_mes'),
    status_operacao_outro_texto: valorOuNulo('status_operacao_outro_texto'),
    possui_hidrometro: document.getElementById('possui_hidrometro').value,
    hidrometro_quantos: valorOuNulo('hidrometro_quantos'),
    hidrometro_1_numero: valorOuNulo('hidrometro_1_numero'),
    hidrometro_1_faturamento: valorOuNulo('hidrometro_1_faturamento'),
    hidrometro_2_numero: valorOuNulo('hidrometro_2_numero'),
    hidrometro_2_faturamento: valorOuNulo('hidrometro_2_faturamento'),
    possui_poco_artesiano: document.getElementById('possui_poco_artesiano').value,
    poco_possui_outorga: valorOuNulo('poco_possui_outorga'),
    outorga_vigencia: valorOuNulo('outorga_vigencia'),
    outorga_vazao: valorOuNulo('outorga_vazao'),
    responsavel_abastecimento: document.getElementById('responsavel_abastecimento').value,
    responsavel_abastecimento_municipio: valorOuNulo('responsavel_abastecimento_municipio'),
    possui_ete: document.getElementById('possui_ete').value,
    ete_ativa: valorOuNulo('ete_ativa'),
    possui_medidor_vazao: document.getElementById('possui_medidor_vazao').value,
    medidor_vazao_outro_texto: valorOuNulo('medidor_vazao_outro_texto'),
    responsavel_esgoto: document.getElementById('responsavel_esgoto').value,
    responsavel_esgoto_outro_texto: valorOuNulo('responsavel_esgoto_outro_texto'),
    licenca_previa: document.getElementById('licenca_previa').value,
    licenca_previa_vigencia: valorOuNulo('licenca_previa_vigencia'),
    licenca_instalacao: document.getElementById('licenca_instalacao').value,
    licenca_instalacao_vigencia: valorOuNulo('licenca_instalacao_vigencia'),
    licenca_operacao: document.getElementById('licenca_operacao').value,
    licenca_operacao_vigencia: valorOuNulo('licenca_operacao_vigencia'),
    licenciamento_bombeiros: document.getElementById('licenciamento_bombeiros').value,
    licenciamento_bombeiros_vigencia: valorOuNulo('licenciamento_bombeiros_vigencia'),
    certidao_uso_solo: document.getElementById('certidao_uso_solo').value,
    certidao_uso_solo_vigencia: valorOuNulo('certidao_uso_solo_vigencia'),
    alvara_sanitario: document.getElementById('alvara_sanitario').value,
    alvara_sanitario_vigencia: valorOuNulo('alvara_sanitario_vigencia'),
    responsavel_tecnico_nome: document.getElementById('responsavel_tecnico_nome').value.trim(),
    responsavel_tecnico_registro: document.getElementById('responsavel_tecnico_registro').value.trim(),
    g_recaptcha_response: typeof grecaptcha !== 'undefined' ? grecaptcha.getResponse() : '',
  };

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/anexo-ix`, {
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
    document.querySelectorAll('[id$="-wrapper"], #hidrometro-detalhes, #outorga-detalhes').forEach((el) => (el.hidden = true));
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

// Restrições deste formulário
restringirCampo(document.getElementById('responsavel_tecnico_nome'), formatarNomePessoa);
