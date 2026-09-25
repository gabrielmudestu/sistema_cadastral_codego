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
const documentosRequerimentoEl = document.getElementById('documentos-requerimento');
const documentosListaEl = document.getElementById('documentos-lista');

const TIPOS_DOCUMENTO_PERMITIDOS = ['application/pdf', 'image/png', 'image/jpeg'];
const EXTENSOES_DOCUMENTO_PERMITIDAS = ['.pdf', '.png', '.jpg', '.jpeg'];

let processoResolvido = null; // { id, status, usuario_nome }
let documentosExigidos = []; // [{ codigo, descricao }] — documentos marcados no formulário

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
  mostrarDocumentosExigidos([]);
}

function escaparHtml(texto) {
  const div = document.createElement('div');
  div.textContent = texto;
  return div.innerHTML;
}

// Um campo de arquivo para cada documento que a pessoa marcou no formulário.
function mostrarDocumentosExigidos(documentos) {
  documentosExigidos = documentos;
  documentosListaEl.innerHTML = documentos
    .map(
      ({ codigo, descricao }) => `
      <div class="field">
        <label for="documento-${codigo}">${escaparHtml(descricao)}</label>
        <div class="file-drop">
          <input type="file" id="documento-${codigo}" data-codigo="${codigo}" accept="application/pdf,image/png,image/jpeg">
          <p class="file-drop__selected" hidden></p>
        </div>
        <p class="field__error" data-error-for="documento-${codigo}"></p>
      </div>`
    )
    .join('');
  documentosRequerimentoEl.hidden = documentos.length === 0;

  documentosListaEl.querySelectorAll('input[type="file"]').forEach((input) => {
    input.addEventListener('change', () => {
      const selecionadoEl = input.parentElement.querySelector('.file-drop__selected');
      const file = input.files[0];
      selecionadoEl.hidden = !file;
      if (file) {
        selecionadoEl.textContent = `Selecionado: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`;
      }
      clearError(input.id);
    });
  });
}

async function buscarDocumentosExigidos(processoId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/${processoId}/documentos-exigidos`);
    return response.ok ? await response.json() : [];
  } catch (error) {
    return [];
  }
}

function validarDocumentos() {
  let valido = true;
  documentosExigidos.forEach(({ codigo }) => {
    const campo = `documento-${codigo}`;
    const file = document.getElementById(campo).files[0];
    const nomeArquivo = (file?.name || '').toLowerCase();
    if (!file) {
      setError(campo, 'Anexe este documento.');
      valido = false;
    } else if (
      !EXTENSOES_DOCUMENTO_PERMITIDAS.some((ext) => nomeArquivo.endsWith(ext)) ||
      !TIPOS_DOCUMENTO_PERMITIDOS.includes(file.type)
    ) {
      setError(campo, 'O arquivo deve ser PDF, PNG ou JPG.');
      valido = false;
    } else if (file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
      setError(campo, `O arquivo excede o limite de ${MAX_UPLOAD_SIZE_MB}MB.`);
      valido = false;
    } else {
      clearError(campo);
    }
  });
  return valido;
}

function irParaPrimeiroErro() {
  const campo = form.querySelector('.field--invalid');
  if (campo) {
    campo.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
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
  // Mesmo protocolo já localizado: não recarrega (apagaria os arquivos já escolhidos).
  if (processoResolvido && processoResolvido.protocolo === protocolo) {
    return;
  }
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
  mostrarDocumentosExigidos(await buscarDocumentosExigidos(processo.id));

  // busca o nome do requerente para exibir no card de confirmação
  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/${processo.id}`);
    const processoDetalhado = await response.json();
    const dados = processoDetalhado.dados_formulario || {};
    mostrarProcessoInfo(
      processo,
      dados.nome_empresarial || dados.nome_empresa || dados.razao_social || `Processo #${processo.id}`
    );
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
    irParaPrimeiroErro();
    return;
  }

  // Localiza o processo antes de validar: é ele que define os documentos exigidos.
  try {
    await resolverProtocolo();
  } catch (error) {
    showFeedback(
      `<p class="feedback__title">Falha de conexão</p><p>Não foi possível falar com o servidor. Verifique se a API está em execução e tente novamente.</p>`,
      'error'
    );
    return;
  }
  if (!processoResolvido) {
    irParaPrimeiroErro(); // erro já mostrado no campo protocolo
    return;
  }

  const file = arquivoInput.files[0];
  const arquivoValido = validarArquivo(file);
  const documentosValidos = validarDocumentos();
  if (!arquivoValido || !documentosValidos) {
    irParaPrimeiroErro();
    return;
  }

  if (typeof grecaptcha !== 'undefined' && !grecaptcha.getResponse()) {
    setError('recaptcha', 'Confirme que você não é um robô.');
    return;
  }
  clearError('recaptcha');

  setLoading(true);

  try {
    const formData = new FormData();
    formData.append('arquivo', file);
    documentosExigidos.forEach(({ codigo }) => {
      formData.append('documentos', document.getElementById(`documento-${codigo}`).files[0]);
      formData.append('documentos_codigos', codigo);
    });
    formData.append(
      'g_recaptcha_response',
      typeof grecaptcha !== 'undefined' ? grecaptcha.getResponse() : ''
    );

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

    const avisoEmail = data.email_enviado
      ? `<p class="feedback__email-status feedback__email-status--ok">✓ Uma cópia foi enviada para ${data.email_destinatario}.</p>`
      : `<p class="feedback__email-status feedback__email-status--warn">O documento foi salvo, mas não foi possível enviar a cópia por e-mail.${data.email_erro ? ` <code>${data.email_erro}</code>` : ''}</p>`;

    const documentosRecebidos = data.documentos_recebidos || [];
    const avisoDocumentos = documentosRecebidos.length
      ? `<p>Documentos recebidos:</p><ul>${documentosRecebidos.map((d) => `<li>${escaparHtml(d)}</li>`).join('')}</ul>`
      : '';

    showFeedback(
      `<p class="feedback__title">Documento assinado recebido com sucesso</p>
       <p>O processo de protocolo <strong>${protocolo}</strong> está agora com status <strong>${data.status}</strong>.</p>
       ${avisoDocumentos}
       ${avisoEmail}
       <div class="feedback__actions">
         <a class="feedback__link" href="recibo.html?protocolo=${encodeURIComponent(protocolo)}">Ver recibo eletrônico →</a>
       </div>`,
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
    if (typeof grecaptcha !== 'undefined') {
      grecaptcha.reset();
    }
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
