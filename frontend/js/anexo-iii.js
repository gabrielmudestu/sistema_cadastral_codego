const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';

const form = document.getElementById('form-anexo-iii');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');

function onlyDigits(value) {
  return value.replace(/\D/g, '');
}

// Número no formato brasileiro ("12.500", "2.500,75", "12500 m²") -> número, ou NaN.
function numeroBr(value) {
  const texto = value.trim().replace(/\s*m\s*[²2]\s*$/i, '');
  if (!/^(\d{1,3}(\.\d{3})*(,\d+)?|\d+(,\d+)?)$/.test(texto)) return NaN;
  return Number(texto.replace(/\./g, '').replace(',', '.'));
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

// RG muda de formato por estado (pode ter letras e o órgão emissor); exige 5 a 14 números.
function rgValido(value) {
  const n = onlyDigits(value).length;
  return n >= 5 && n <= 14;
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
document.getElementById('representante_cpf').addEventListener('input', (e) => {
  e.target.value = maskCpf(onlyDigits(e.target.value));
});

function maskCep(digits) {
  return digits.slice(0, 8).replace(/(\d{5})(\d{1,3})$/, '$1-$2');
}

function configurarBuscaCep(cepInputId, statusId, enderecoInputId, campoErro) {
  const cepInput = document.getElementById(cepInputId);
  const statusEl = document.getElementById(statusId);
  const enderecoInput = document.getElementById(enderecoInputId);

  cepInput.addEventListener('input', (e) => {
    e.target.value = maskCep(onlyDigits(e.target.value));
    statusEl.textContent = '';
    statusEl.className = 'field__hint';
  });

  cepInput.addEventListener('blur', async () => {
    const cepDigits = onlyDigits(cepInput.value);
    if (cepDigits.length !== 8) {
      return;
    }

    statusEl.textContent = 'Buscando endereço...';
    statusEl.className = 'field__hint';

    try {
      const response = await fetch(`https://viacep.com.br/ws/${cepDigits}/json/`);
      const dados = await response.json();

      if (dados.erro) {
        statusEl.textContent = 'CEP não encontrado. Preencha o endereço manualmente.';
        statusEl.className = 'field__hint field__hint--warn';
        return;
      }

      const partes = [dados.logradouro, dados.bairro, `${dados.localidade}-${dados.uf}`]
        .filter((parte) => parte && parte.trim());
      const enderecoEncontrado = partes.join(', ');

      if (!enderecoInput.value.trim()) {
        enderecoInput.value = enderecoEncontrado;
      }

      statusEl.textContent = `Endereço encontrado: ${enderecoEncontrado}. Complete com número/complemento, se necessário.`;
      statusEl.className = 'field__hint field__hint--ok';
      clearError(campoErro);
    } catch (error) {
      statusEl.textContent = 'Não foi possível consultar o CEP agora. Preencha o endereço manualmente.';
      statusEl.className = 'field__hint field__hint--warn';
    }
  });
}

configurarBuscaCep(
  'cep_busca',
  'cep_busca-status',
  'endereco_correspondencia_empresa',
  'endereco_correspondencia_empresa'
);
configurarBuscaCep(
  'representante_cep_busca',
  'representante_cep_busca-status',
  'representante_endereco_correspondencia',
  'representante_endereco_correspondencia'
);

// Linhas de CNAE com algum campo preenchido (linhas totalmente vazias são ignoradas).
function coletarCnaes() {
  return Array.from(document.querySelectorAll('#cnaes-group .cnae-row'))
    .map((linha) => ({
      numero: linha.querySelector('[data-cnae="numero"]').value.trim(),
      descricao: linha.querySelector('[data-cnae="descricao"]').value.trim(),
    }))
    .filter((cnae) => cnae.numero || cnae.descricao);
}

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

// RG: letras (órgão emissor), números e separadores; no máximo 14 números
// (o que passar disso, inclusive ao colar, é cortado).
function formatarRg(v) {
  let numeros = 0;
  return [...v.replace(/[^\p{L}\d\s./-]/gu, '').toUpperCase()]
    .filter((c) => !/\d/.test(c) || (numeros += 1) <= 14)
    .join('');
}

// Número no formato brasileiro, formatado enquanto digita: "12500" -> "12.500",
// com vírgula para decimais (até 2 casas).
function formatarNumeroBr(v) {
  const [inteiro, ...decimais] = v.replace(/[^\d,]/g, '').split(',');
  const milhares = inteiro.replace(/^0+(?=\d)/, '').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return decimais.length ? `${milhares},${decimais.join('').slice(0, 2)}` : milhares;
}

// CNAE: só números, formatado como 1091-1/01.
const formatarCnae = (v) => onlyDigits(v).slice(0, 7)
  .replace(/^(\d{4})(\d)/, '$1-$2')
  .replace(/^(\d{4}-\d)(\d{1,2})/, '$1/$2');

function validateEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

const CAMPOS_TEXTO_OBRIGATORIOS = [
  ['municipio_interesse', 'Informe o município de interesse.'],
  ['metragem_necessaria', 'Informe a metragem necessária.'],
  ['nome_empresarial', 'Informe o nome empresarial.'],
  ['endereco_correspondencia_empresa', 'Informe o endereço para correspondência da empresa.'],
  ['representante_nome', 'Informe o nome do representante.'],
  ['representante_rg', 'Informe o RG do representante.'],
  ['representante_nome_mae', 'Informe o nome da mãe do representante.'],
  ['representante_endereco_correspondencia', 'Informe o endereço para correspondência do representante.'],
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
  } else if (!cnpjValido(cnpjDigits)) {
    setError('cnpj', 'CNPJ inválido. Confira os números digitados.');
    valid = false;
  } else {
    clearError('cnpj');
  }

  const cpfDigits = onlyDigits(document.getElementById('representante_cpf').value);
  if (cpfDigits.length !== 11) {
    setError('representante_cpf', 'CPF deve ter 11 dígitos.');
    valid = false;
  } else if (!cpfValido(cpfDigits)) {
    setError('representante_cpf', 'CPF inválido. Confira os números digitados.');
    valid = false;
  } else {
    clearError('representante_cpf');
  }

  const emailValue = document.getElementById('email').value.trim();
  if (!validateEmail(emailValue)) {
    setError('email', 'Informe um e-mail válido.');
    valid = false;
  } else {
    clearError('email');
  }

  // Um ou mais telefones separados por "/", "," ou ";", cada um com DDD.
  const telefones = document.getElementById('telefones').value
    .split(/[/,;]/)
    .map((parte) => onlyDigits(parte))
    .filter((digits) => digits.length > 0);
  if (telefones.length === 0) {
    setError('telefones', 'Informe ao menos um telefone com DDD.');
    valid = false;
  } else if (telefones.length > 3) {
    setError('telefones', 'Informe no máximo 3 telefones.');
    valid = false;
  } else if (telefones.some((digits) => digits.length < 10 || digits.length > 11)) {
    setError('telefones', 'Cada telefone deve ter DDD + número: 10 dígitos (fixo) ou 11 (celular). Separe os números com "/".');
    valid = false;
  } else {
    clearError('telefones');
  }

  // Cada linha de CNAE preenchida precisa ter número e descrição; ao menos uma linha.
  const cnaes = coletarCnaes();
  if (cnaes.some((cnae) => !cnae.numero || !cnae.descricao)) {
    setError('cnaes', 'Preencha o número e a descrição de cada CNAE informado.');
    valid = false;
  } else if (cnaes.length === 0) {
    setError('cnaes', 'Informe ao menos um CNAE.');
    valid = false;
  } else {
    clearError('cnaes');
  }

  const rgValor = document.getElementById('representante_rg').value;
  if (rgValor.trim() && !rgValido(rgValor)) {
    setError('representante_rg', 'RG inválido: informe o número completo do documento (entre 5 e 14 números).');
    valid = false;
  }

  const metragem = document.getElementById('metragem_necessaria').value;
  if (metragem.trim()) {
    const valor = numeroBr(metragem);
    if (Number.isNaN(valor)) {
      setError('metragem_necessaria', 'Informe apenas números (ex.: 12.500 ou 2.500,50).');
      valid = false;
    } else if (valor <= 0) {
      setError('metragem_necessaria', 'A metragem deve ser maior que zero.');
      valid = false;
    }
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

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideFeedback();

  if (!validateForm()) {
    irParaPrimeiroErro();
    return;
  }

  const payload = {
    municipio_interesse: document.getElementById('municipio_interesse').value.trim(),
    metragem_necessaria: document.getElementById('metragem_necessaria').value.trim(),
    nome_empresarial: document.getElementById('nome_empresarial').value.trim(),
    cnpj: document.getElementById('cnpj').value,
    endereco_correspondencia_empresa: document.getElementById('endereco_correspondencia_empresa').value.trim(),
    representante_nome: document.getElementById('representante_nome').value.trim(),
    representante_cpf: document.getElementById('representante_cpf').value,
    representante_rg: document.getElementById('representante_rg').value.trim(),
    representante_nome_mae: document.getElementById('representante_nome_mae').value.trim(),
    email: document.getElementById('email').value.trim(),
    telefones: document.getElementById('telefones').value.trim(),
    representante_endereco_correspondencia: document.getElementById('representante_endereco_correspondencia').value.trim(),
    cnaes: coletarCnaes(),
    documentos: Array.from(document.querySelectorAll('input[name="documentos"]:checked')).map((el) => el.value),
    g_recaptcha_response: typeof grecaptcha !== 'undefined' ? grecaptcha.getResponse() : '',
  };

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/anexo-iii`, {
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

// Restrições deste formulário
restringirCampo(document.getElementById('representante_nome'), formatarNomePessoa);
restringirCampo(document.getElementById('representante_nome_mae'), formatarNomePessoa);
restringirCampo(document.getElementById('representante_rg'), formatarRg);
restringirCampo(document.getElementById('metragem_necessaria'), formatarNumeroBr);
document.querySelectorAll('[data-cnae="numero"]').forEach((el) => restringirCampo(el, formatarCnae));
// Telefones: números, parênteses, hífen, espaço e "/" entre números; até 3 números de 11 dígitos.
restringirCampo(
  document.getElementById('telefones'),
  (v) => v.replace(/[^\d\s()/-]/g, ''),
  (v) => v.split('/').length <= 3 && v.split('/').every((parte) => onlyDigits(parte).length <= 11)
);
