const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';

const form = document.getElementById('form-anexo-viii-d');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');
const checkOutros = document.getElementById('check-outros');
const outrosWrapper = document.getElementById('outros-texto-wrapper');
const outrosInput = document.getElementById('outros_texto');

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
document.getElementById('representante_cpf').addEventListener('input', (e) => {
  e.target.value = maskCpf(onlyDigits(e.target.value));
});
document.getElementById('telefone').addEventListener('input', (e) => {
  e.target.value = maskTelefone(onlyDigits(e.target.value));
});

checkOutros.addEventListener('change', () => {
  outrosWrapper.hidden = !checkOutros.checked;
  if (!checkOutros.checked) {
    outrosInput.value = '';
    clearError('outros_texto');
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
  ['processo_numero', 'Informe o número do processo.'],
  ['nome_empresarial', 'Informe o nome empresarial.'],
  ['endereco', 'Informe o endereço da empresa.'],
  ['representante_nome', 'Informe o nome do representante legal.'],
  ['representante_rg', 'Informe o RG do representante legal.'],
  ['representante_endereco', 'Informe o endereço do representante legal.'],
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

  const estadoCivil = document.getElementById('representante_estado_civil').value;
  if (!estadoCivil) {
    setError('representante_estado_civil', 'Selecione o estado civil.');
    valid = false;
  } else {
    clearError('representante_estado_civil');
  }

  const cpfDigits = onlyDigits(document.getElementById('representante_cpf').value);
  if (cpfDigits.length !== 11) {
    setError('representante_cpf', 'CPF deve ter 11 dígitos.');
    valid = false;
  } else {
    clearError('representante_cpf');
  }

  const solicitacoesMarcadas = Array.from(
    document.querySelectorAll('input[name="solicitacoes"]:checked')
  ).map((el) => el.value);

  if (solicitacoesMarcadas.length === 0) {
    setError('solicitacoes', 'Selecione ao menos uma solicitação.');
    valid = false;
  } else {
    clearError('solicitacoes');
  }

  if (solicitacoesMarcadas.includes('outros') && !outrosInput.value.trim()) {
    setError('outros_texto', 'Descreva a solicitação em "Outros".');
    valid = false;
  } else {
    clearError('outros_texto');
  }

  const motivacaoValue = document.getElementById('motivacao').value.trim();
  if (!motivacaoValue) {
    setError('motivacao', 'Descreva a motivação da solicitação.');
    valid = false;
  } else {
    clearError('motivacao');
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
    return;
  }

  const solicitacoes = Array.from(
    document.querySelectorAll('input[name="solicitacoes"]:checked')
  ).map((el) => el.value);

  const payload = {
    processo_numero: document.getElementById('processo_numero').value.trim(),
    nome_empresarial: document.getElementById('nome_empresarial').value.trim(),
    cnpj: document.getElementById('cnpj').value,
    endereco: document.getElementById('endereco').value.trim(),
    telefone: document.getElementById('telefone').value,
    email: document.getElementById('email').value.trim(),
    representante_nome: document.getElementById('representante_nome').value.trim(),
    representante_estado_civil: document.getElementById('representante_estado_civil').value,
    representante_rg: document.getElementById('representante_rg').value.trim(),
    representante_cpf: document.getElementById('representante_cpf').value,
    representante_endereco: document.getElementById('representante_endereco').value.trim(),
    solicitacoes: solicitacoes,
    outros_texto: outrosInput.value.trim() || null,
    motivacao: document.getElementById('motivacao').value.trim(),
  };

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/anexo-viii-d`, {
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
       <div class="feedback__actions">
         <a class="feedback__link" href="${pdfUrl}" target="_blank" rel="noopener">Baixar documento PDF</a>
         <a class="feedback__link feedback__link--secondary" href="upload-assinado.html?protocolo=${encodeURIComponent(protocolo)}">Já assinei, enviar documento →</a>
       </div>`,
      'success'
    );

    form.reset();
    outrosWrapper.hidden = true;
  } catch (error) {
    showFeedback(
      `<p class="feedback__title">Falha de conexão</p><p>Não foi possível falar com o servidor. Verifique se a API está em execução e tente novamente.</p>`,
      'error'
    );
  } finally {
    setLoading(false);
  }
});
