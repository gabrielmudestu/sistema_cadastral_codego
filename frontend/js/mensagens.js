const API_BASE_URL = window.CODEGO_API_BASE_URL; // definido em js/config.js
const MAX_ANEXO_SIZE_MB = 10;
const EXTENSOES_ANEXO_PERMITIDAS = ['.pdf', '.png', '.jpg', '.jpeg'];

const form = document.getElementById('form-mensagem');
const submitButton = document.getElementById('btn-submit');
const feedbackEl = document.getElementById('feedback');
const protocoloInput = document.getElementById('protocolo');
const anexosInput = document.getElementById('anexos');
const anexosSelecionadoEl = document.getElementById('anexos-selecionado');
const processoInfoEl = document.getElementById('processo-info');
const processoInfoNomeEl = document.getElementById('processo-info-nome');
const processoInfoStatusEl = document.getElementById('processo-info-status');
const historicoWrapper = document.getElementById('historico-wrapper');
const historicoLista = document.getElementById('historico-lista');

let processoResolvido = null;

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

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? 'Enviando…' : 'Enviar mensagem';
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

async function resolverProtocolo() {
  const protocolo = protocoloInput.value.trim();
  esconderProcessoInfo();
  historicoWrapper.hidden = true;

  if (!protocolo) return;

  const response = await fetch(`${API_BASE_URL}/api/processos/protocolo/${encodeURIComponent(protocolo)}`);
  if (!response.ok) {
    setError('protocolo', 'Protocolo não encontrado. Confira o número e tente novamente.');
    return;
  }
  clearError('protocolo');
  const processo = await response.json();
  processoResolvido = processo;

  try {
    const detalhado = await fetch(`${API_BASE_URL}/api/cadastro/${processo.id}`);
    const dados = await detalhado.json();
    mostrarProcessoInfo(processo, (dados.dados_formulario || {}).nome_empresarial || `Processo #${processo.id}`);
  } catch (error) {
    mostrarProcessoInfo(processo, `Processo #${processo.id}`);
  }

  carregarHistorico(processo.id);
}

function formatarData(isoString) {
  const data = new Date(isoString);
  return data.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function formatarTamanho(bytes) {
  return `${(bytes / 1024).toFixed(0)}KB`;
}

async function carregarHistorico(processoId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/mensagens/${processoId}`);
    if (!response.ok) return;
    const mensagens = await response.json();

    historicoLista.innerHTML = '';
    if (mensagens.length === 0) {
      historicoWrapper.hidden = true;
      return;
    }

    mensagens
      .slice()
      .reverse()
      .forEach((msg) => {
        const item = document.createElement('div');
        item.className = 'mensagem-item';

        const anexosHtml = (msg.anexos || [])
          .map((a) => `<span>📎 ${a.nome_original} (${formatarTamanho(a.tamanho_bytes)})</span>`)
          .join('');

        item.innerHTML = `
          <div class="mensagem-item__cabecalho">
            <span class="mensagem-item__assunto">${msg.assunto}</span>
            <span class="mensagem-item__data">${formatarData(msg.data_envio)}</span>
          </div>
          <p class="mensagem-item__remetente">De: ${msg.remetente_nome}</p>
          <p class="mensagem-item__conteudo">${msg.conteudo}</p>
          ${anexosHtml ? `<div class="mensagem-item__anexos">${anexosHtml}</div>` : ''}
        `;
        historicoLista.appendChild(item);
      });

    historicoWrapper.hidden = false;
  } catch (error) {
    // silencioso — histórico é um extra, não deve travar a tela
  }
}

protocoloInput.addEventListener('blur', resolverProtocolo);

anexosInput.addEventListener('change', () => {
  const files = Array.from(anexosInput.files);
  if (files.length === 0) {
    anexosSelecionadoEl.hidden = true;
    return;
  }
  anexosSelecionadoEl.textContent = `Selecionados: ${files.map((f) => f.name).join(', ')}`;
  anexosSelecionadoEl.hidden = false;
});

function validarAnexos() {
  const files = Array.from(anexosInput.files);
  for (const file of files) {
    const nomeArquivo = file.name.toLowerCase();
    const extensaoValida = EXTENSOES_ANEXO_PERMITIDAS.some((ext) => nomeArquivo.endsWith(ext));
    if (!extensaoValida) {
      showFeedback(
        `<p class="feedback__title">Anexo inválido</p><p>"${file.name}" deve ser PDF, PNG ou JPG.</p>`,
        'error'
      );
      return false;
    }
    if (file.size > MAX_ANEXO_SIZE_MB * 1024 * 1024) {
      showFeedback(
        `<p class="feedback__title">Anexo muito grande</p><p>"${file.name}" excede o limite de ${MAX_ANEXO_SIZE_MB}MB.</p>`,
        'error'
      );
      return false;
    }
  }
  return true;
}

function validateForm() {
  let valid = true;

  if (!document.getElementById('remetente_nome').value.trim()) {
    setError('remetente_nome', 'Informe o nome do remetente.');
    valid = false;
  } else {
    clearError('remetente_nome');
  }

  if (!document.getElementById('assunto').value.trim()) {
    setError('assunto', 'Informe o assunto.');
    valid = false;
  } else {
    clearError('assunto');
  }

  if (!document.getElementById('conteudo').value.trim()) {
    setError('conteudo', 'Escreva a mensagem.');
    valid = false;
  } else {
    clearError('conteudo');
  }

  if (!validarAnexos()) {
    valid = false;
  }

  if (typeof grecaptcha !== 'undefined' && !grecaptcha.getResponse()) {
    setError('recaptcha', 'Confirme que você não é um robô.');
    valid = false;
  } else {
    clearError('recaptcha');
  }

  return valid;
}

function extrairMensagemErro(payload) {
  if (!payload) return 'Não foi possível enviar a mensagem. Tente novamente.';
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((erro) => erro.msg || 'Campo inválido.').join(' ');
  }
  return 'Não foi possível enviar a mensagem. Tente novamente.';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideFeedback();

  if (!validateForm()) return;

  const formData = new FormData();
  formData.append('remetente_nome', document.getElementById('remetente_nome').value.trim());
  formData.append('assunto', document.getElementById('assunto').value.trim());
  formData.append('conteudo', document.getElementById('conteudo').value.trim());
  if (processoResolvido) {
    formData.append('processo_id', processoResolvido.id);
  }
  const protocoloValor = protocoloInput.value.trim();
  if (protocoloValor) {
    formData.append('protocolo', protocoloValor);
  }
  Array.from(anexosInput.files).forEach((file) => {
    formData.append('anexos', file);
  });
  formData.append(
    'g_recaptcha_response',
    typeof grecaptcha !== 'undefined' ? grecaptcha.getResponse() : ''
  );

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/mensagens`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      showFeedback(
        `<p class="feedback__title">Não foi possível enviar a mensagem</p><p>${extrairMensagemErro(data)}</p>`,
        'error'
      );
      return;
    }

    showFeedback(
      `<p class="feedback__title">Mensagem enviada com sucesso</p>
       <p>${data.anexos && data.anexos.length ? `${data.anexos.length} anexo(s) enviado(s) junto com a mensagem.` : 'Nenhum anexo enviado.'}</p>`,
      'success'
    );

    document.getElementById('remetente_nome').value = '';
    document.getElementById('assunto').value = '';
    document.getElementById('conteudo').value = '';
    anexosInput.value = '';
    anexosSelecionadoEl.hidden = true;

    if (processoResolvido) {
      carregarHistorico(processoResolvido.id);
    }
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

window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const protocoloParam = params.get('protocolo');
  if (protocoloParam) {
    protocoloInput.value = protocoloParam;
    resolverProtocolo();
  }
});
