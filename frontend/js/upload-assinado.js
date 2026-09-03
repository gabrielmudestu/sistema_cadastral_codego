const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';
const MAX_UPLOAD_SIZE_MB = 10;

const form = document.getElementById('form-upload');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');
const protocoloInput = document.getElementById('protocolo');
const arquivoInput = document.getElementById('arquivo');
const arquivoSelecionadoEl = document.getElementById('arquivo-selecionado');
const processoInfoEl = document.getElementById('processo-info');
const processoInfoNomeEl = document.getElementById('processo-info-nome');
const processoInfoStatusEl = document.getElementById('processo-info-status');

let processoResolvido = null; // { id, status, usuario_nome }

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
  feedbackEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideFeedback() {
  feedbackEl.hidden = true;
  feedbackEl.innerHTML = '';
}

function esconderProcessoInfo() {
  processoInfoEl.hidden = true;
  processoResolvido = null;
}

function mostrarProcessoInfo(processo, nomeUsuario) {
  processoInfoNomeEl.textContent = nomeUsuario;
  processoInfoStatusEl.textContent = processo.status;
  processoInfoStatusEl.className =
    'processo-info__status' + (processo.status === 'Assinado' ? ' processo-info__status--assinado' : '');
  processoInfoEl.hidden = false;
}

async function buscarProcessoPorProtocolo(protocolo) {
  const response = await fetch(`${API_BASE_URL}/api/processos/protocolo/${encodeURIComponent(protocolo)}`);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

async function resolverProtocolo() {
  const protocolo = protocoloInput.value.trim();
  esconderProcessoInfo();

  if (!protocolo) {
    return;
  }

  const processo = await buscarProcessoPorProtocolo(protocolo);
  if (!processo) {
    setError('protocolo', 'Protocolo não encontrado. Confira o número e tente novamente.');
    return;
  }

  clearError('protocolo');
  processoResolvido = processo;

  // busca o nome do requerente para exibir no card de confirmação
  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/${processo.id}`);
    const processoDetalhado = await response.json();
    const dados = processoDetalhado.dados_formulario || {};
    mostrarProcessoInfo(processo, dados.nome_empresarial || `Processo #${processo.id}`);
  } catch (error) {
    mostrarProcessoInfo(processo, `Processo #${processo.id}`);
  }
}

protocoloInput.addEventListener('blur', resolverProtocolo);

arquivoInput.addEventListener('change', () => {
  const file = arquivoInput.files[0];
  if (!file) {
    arquivoSelecionadoEl.hidden = true;
    return;
  }
  arquivoSelecionadoEl.textContent = `Selecionado: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`;
  arquivoSelecionadoEl.hidden = false;
  clearError('arquivo');
});

function validarArquivo(file) {
  if (!file) {
    setError('arquivo', 'Selecione o PDF do documento assinado.');
    return false;
  }
  const nomeArquivo = file.name.toLowerCase();
  if (!nomeArquivo.endsWith('.pdf') || file.type !== 'application/pdf') {
    setError('arquivo', 'O arquivo deve estar no formato PDF.');
    return false;
  }
  if (file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
    setError('arquivo', `O arquivo excede o limite de ${MAX_UPLOAD_SIZE_MB}MB.`);
    return false;
  }
  clearError('arquivo');
  return true;
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? 'Enviando…' : 'Enviar documento assinado';
}

function extrairMensagemErro(payload) {
  if (!payload) return 'Não foi possível enviar o documento. Tente novamente.';
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((erro) => erro.msg || 'Campo inválido.').join(' ');
  }
  return 'Não foi possível enviar o documento. Tente novamente.';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideFeedback();

  const protocolo = protocoloInput.value.trim();
  if (!protocolo) {
    setError('protocolo', 'Informe o número do protocolo.');
    return;
  }

  const file = arquivoInput.files[0];
  const arquivoValido = validarArquivo(file);
  if (!arquivoValido) {
    return;
  }

  setLoading(true);

  try {
    if (!processoResolvido || processoResolvido.protocolo !== protocolo) {
      await resolverProtocolo();
    }

    if (!processoResolvido) {
      return; // erro já mostrado no campo protocolo
    }

    const formData = new FormData();
    formData.append('arquivo', file);

    const response = await fetch(`${API_BASE_URL}/api/cadastro/${processoResolvido.id}/assinado`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      showFeedback(
        `<p class="feedback__title">Não foi possível enviar o documento</p><p>${extrairMensagemErro(data)}</p>`,
        'error'
      );
      return;
    }

    showFeedback(
      `<p class="feedback__title">Documento assinado recebido com sucesso</p>
       <p>O processo de protocolo <strong>${protocolo}</strong> está agora com status <strong>${data.status}</strong>.</p>
       <p>O recibo eletrônico deste processo estará disponível na próxima etapa.</p>`,
      'success'
    );

    form.reset();
    arquivoSelecionadoEl.hidden = true;
    esconderProcessoInfo();
  } catch (error) {
    showFeedback(
      `<p class="feedback__title">Falha de conexão</p><p>Não foi possível falar com o servidor. Verifique se a API está em execução e tente novamente.</p>`,
      'error'
    );
  } finally {
    setLoading(false);
  }
});

// Pré-preenche o protocolo se vier por parâmetro na URL (link vindo da Tela 1)
window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const protocoloParam = params.get('protocolo');
  if (protocoloParam) {
    protocoloInput.value = protocoloParam;
    resolverProtocolo();
  }
});
