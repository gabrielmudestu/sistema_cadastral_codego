const form = document.getElementById('form-cadastro');
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

form.addEventListener('submit', (event) => {
  event.preventDefault();

  if (!validateForm()) {
    return;
  }

  const payload = {
    nome: nomeInput.value.trim(),
    tipo_documento: docType,
    documento: onlyDigits(documentoInput.value),
    email: emailInput.value.trim(),
    telefone: onlyDigits(telefoneInput.value),
    cargo: cargoInput.value.trim(),
  };

  // Integração com o back-end (FastAPI) será conectada aqui:
  // fetch('/api/cadastro', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) })
  console.log('Dados prontos para envio ao back-end:', payload);
});
