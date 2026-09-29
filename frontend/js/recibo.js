const API_BASE_URL = window.CODEGO_API_BASE_URL; // definido em js/config.js

const form = document.getElementById('form-recibo');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');
const protocoloInput = document.getElementById('protocolo');
const resultadoEl = document.getElementById('recibo-resultado');
const linkMensagens = document.getElementById('link-mensagens');

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

function showFeedback(html, type) {
  feedbackEl.innerHTML = html;
  feedbackEl.className = `feedback feedback--${type}`;
  feedbackEl.hidden = false;
}

function hideFeedback() {
  feedbackEl.hidden = true;
  feedbackEl.innerHTML = '';
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? 'Consultando…' : 'Consultar recibo';
}

function formatarData(isoString) {
  const data = new Date(isoString);
  return data.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function extrairMensagemErro(payload, statusCode) {
  if (statusCode === 404) return 'Protocolo não encontrado. Confira o número e tente novamente.';
  if (statusCode === 409) {
    return (payload && payload.detail) ||
      'O recibo só fica disponível depois que o documento assinado é recebido (Etapa 2).';
  }
  if (payload && typeof payload.detail === 'string') return payload.detail;
  return 'Não foi possível consultar o recibo. Tente novamente.';
}

async function consultarRecibo(protocolo) {
  hideFeedback();
  resultadoEl.hidden = true;

  // resolve o protocolo -> id do processo
  const respProcesso = await fetch(`${API_BASE_URL}/api/processos/protocolo/${encodeURIComponent(protocolo)}`);
  if (!respProcesso.ok) {
    setError('protocolo', 'Protocolo não encontrado. Confira o número e tente novamente.');
    return;
  }
  clearError('protocolo');
  const processo = await respProcesso.json();

  const respRecibo = await fetch(`${API_BASE_URL}/api/recibo/${processo.id}`);
  const dataRecibo = await respRecibo.json().catch(() => null);

  if (!respRecibo.ok) {
    showFeedback(
      `<p class="feedback__title">Recibo indisponível</p><p>${extrairMensagemErro(dataRecibo, respRecibo.status)}</p>`,
      'error'
    );
    return;
  }

  document.getElementById('recibo-protocolo').textContent = `Protocolo: ${dataRecibo.protocolo}`;
  document.getElementById('recibo-data').textContent = formatarData(dataRecibo.data_hora);
  document.getElementById('recibo-remetente').textContent = dataRecibo.remetente_documento_mascarado
    ? `${dataRecibo.remetente_nome} (${dataRecibo.remetente_documento_mascarado})`
    : dataRecibo.remetente_nome;
  document.getElementById('recibo-documento').textContent = 'Documento cadastral assinado';
  document.getElementById('recibo-declaracao').textContent = dataRecibo.declaracao;

  const listaArquivos = document.getElementById('recibo-arquivos');
  listaArquivos.innerHTML = '';
  (dataRecibo.arquivos || []).forEach((caminho) => {
    const nomeArquivo = caminho.split('/').pop();
    const li = document.createElement('li');
    li.textContent = `📎 ${nomeArquivo}`;
    listaArquivos.appendChild(li);
  });

  linkMensagens.href = `mensagens.html?protocolo=${encodeURIComponent(protocolo)}`;

  resultadoEl.hidden = false;
  resultadoEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const protocolo = protocoloInput.value.trim();
  if (!protocolo) {
    setError('protocolo', 'Informe o número do protocolo.');
    return;
  }
  clearError('protocolo');

  setLoading(true);
  try {
    await consultarRecibo(protocolo);
  } catch (error) {
    showFeedback(
      `<p class="feedback__title">Falha de conexão</p><p>Não foi possível falar com o servidor. Verifique se a API está em execução e tente novamente.</p>`,
      'error'
    );
  } finally {
    setLoading(false);
  }
});

document.getElementById('btn-imprimir').addEventListener('click', () => {
  window.print();
});

window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const protocoloParam = params.get('protocolo');
  if (protocoloParam) {
    protocoloInput.value = protocoloParam;
    form.dispatchEvent(new Event('submit', { cancelable: true }));
  }
});
