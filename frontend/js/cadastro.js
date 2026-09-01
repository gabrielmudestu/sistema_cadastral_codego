// URL base da API. Em produção, ajustar para o domínio real do backend.
const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';

const form = document.getElementById('form-cadastro');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');
const nomeInput = document.getElementById('nome');
const documentoInput = document.getElementById('documento');
const emailInput = document.getElementById('email');
const telefoneInput = document.getElementById('telefone');
const cargoInput = document.getElementById('cargo');
const docToggleButtons = document.querySelectorAll('[data-doc-type]');

let docType = 'cpf';

function onlyDigits(value) {
  return value.replace(/\D/g, '');
}

function maskCpf(digits) {
  return digits
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
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

function setDocType(type) {
  docType = type;
  docToggleButtons.forEach((btn) => {
    btn.classList.toggle('is-active', btn.dataset.docType === type);
  });
  documentoInput.placeholder = type === 'cpf' ? '000.000.000-00' : '00.000.000/0000-00';
  documentoInput.value = '';
  clearError('documento');
}

docToggleButtons.forEach((btn) => {
  btn.addEventListener('click', () => setDocType(btn.dataset.docType));
});

documentoInput.addEventListener('input', (event) => {
  const digits = onlyDigits(event.target.value);
  event.target.value = docType === 'cpf' ? maskCpf(digits) : maskCnpj(digits);
});

telefoneInput.addEventListener('input', (event) => {
  event.target.value = maskTelefone(onlyDigits(event.target.value));
});

function setError(fieldName, message) {
  const field = document.getElementById(fieldName);
  const errorEl = document.querySelector(`[data-error-for="${fieldName}"]`);
  field.closest('.field').classList.add('field--invalid');
  errorEl.textContent = message;
}

function clearError(fieldName) {
  const field = document.getElementById(fieldName);
  const errorEl = document.querySelector(`[data-error-for="${fieldName}"]`);
  field.closest('.field').classList.remove('field--invalid');
  errorEl.textContent = '';
}

function validateEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function validateForm() {
  let valid = true;

  if (!nomeInput.value.trim()) {
    setError('nome', 'Informe o nome completo.');
    valid = false;
  } else {
    clearError('nome');
  }

  const docDigits = onlyDigits(documentoInput.value);
  const expectedLength = docType === 'cpf' ? 11 : 14;
  if (docDigits.length !== expectedLength) {
    setError('documento', docType === 'cpf' ? 'CPF deve ter 11 dígitos.' : 'CNPJ deve ter 14 dígitos.');
    valid = false;
  } else {
    clearError('documento');
  }

  if (!validateEmail(emailInput.value.trim())) {
    setError('email', 'Informe um e-mail válido.');
    valid = false;
  } else {
    clearError('email');
  }

  const telDigits = onlyDigits(telefoneInput.value);
  if (telDigits.length < 10) {
    setError('telefone', 'Informe um telefone válido, com DDD.');
    valid = false;
  } else {
    clearError('telefone');
  }

  if (!cargoInput.value.trim()) {
    setError('cargo', 'Informe o cargo ou representação.');
    valid = false;
  } else {
    clearError('cargo');
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
    return payload.detail
      .map((erro) => erro.msg || 'Campo inválido.')
      .join(' ');
  }
  return 'Não foi possível processar o cadastro. Tente novamente.';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideFeedback();

  if (!validateForm()) {
    return;
  }

  const payload = {
    nome: nomeInput.value.trim(),
    tipo_documento: docType,
    documento: documentoInput.value,
    email: emailInput.value.trim(),
    telefone: telefoneInput.value,
    cargo: cargoInput.value.trim(),
  };

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro`, {
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
       <a class="feedback__link" href="${pdfUrl}" target="_blank" rel="noopener">Baixar documento PDF</a>`,
      'success'
    );

    form.reset();
    setDocType('cpf');
  } catch (error) {
    showFeedback(
      `<p class="feedback__title">Falha de conexão</p><p>Não foi possível falar com o servidor. Verifique se a API está em execução e tente novamente.</p>`,
      'error'
    );
  } finally {
    setLoading(false);
  }
});
