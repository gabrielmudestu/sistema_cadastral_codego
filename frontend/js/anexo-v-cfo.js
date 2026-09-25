const API_BASE_URL = window.CODEGO_API_BASE_URL || 'http://localhost:8000';

const form = document.getElementById('form-anexo-v-cfo');
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

configurarBuscaCep('cep_busca', 'cep_busca-status', 'endereco', 'endereco');

// ---------------------------------------------------------------------------
// Cronograma: serviços (linhas) x meses da obra (colunas).
// O estado fica em memória; a tabela só é redesenhada quando a estrutura muda
// (período alterado, serviço adicionado/removido), para não perder o foco
// enquanto o usuário digita.
// ---------------------------------------------------------------------------

// Mesma lista de serviços do modelo oficial do cronograma.
const SERVICOS_SUGERIDOS = [
  'Serviços preliminares',
  'Infraestrutura',
  'Paredes e Painéis',
  'Cobertura',
  'Pavimentação',
];
const MAX_MESES = 60;
const MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

const cronogramaEl = document.getElementById('cronograma');
const adicionarServicoWrapper = document.getElementById('adicionar-servico-wrapper');
const inicioInput = document.getElementById('inicio_obras');
const terminoInput = document.getElementById('termino_obras');

let servicos = SERVICOS_SUGERIDOS.map((descricao) => ({ descricao, percentuais: [] }));

// Quantidade de meses entre início e término (inclusive). 0 se o período ainda
// não foi informado ou é inválido.
function totalMeses() {
  if (!inicioInput.value || !terminoInput.value) return 0;
  const [anoI, mesI] = inicioInput.value.split('-').map(Number);
  const [anoT, mesT] = terminoInput.value.split('-').map(Number);
  const meses = (anoT - anoI) * 12 + (mesT - mesI) + 1;
  return meses >= 1 && meses <= MAX_MESES ? meses : 0;
}

// Mensagem de erro do período informado, ou '' se estiver coerente (ou incompleto).
const hoje = new Date();
const MES_ATUAL = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`;
inicioInput.min = MES_ATUAL;

function problemaInicio() {
  return inicioInput.value && inicioInput.value < MES_ATUAL
    ? 'A previsão de início das obras não pode ser um mês que já passou.'
    : '';
}

function problemaPeriodo() {
  const inicio = inicioInput.value;
  const termino = terminoInput.value;
  if (!inicio || !termino) return '';
  if (termino < inicio) {
    return 'A previsão de término deve ser igual ou posterior à previsão de início.';
  }
  if (totalMeses() === 0) {
    return `O cronograma pode ter no máximo ${MAX_MESES} meses (5 anos).`;
  }
  return '';
}

// Valida o período assim que uma das datas muda, e limita o calendário para
// não permitir escolher um término antes do início (e vice-versa).
// Datas que não fazem sentido (início no passado, término antes do início,
// mais de 5 anos) não são aceitas: o campo volta ao valor anterior.
let inicioAnterior = '';
let terminoAnterior = '';
function atualizarPeriodo() {
  inicioAnterior = inicioInput.value;
  terminoAnterior = terminoInput.value;
  terminoInput.min = inicioInput.value || MES_ATUAL;
  inicioInput.max = terminoInput.value || '';
  renderCronograma();
}
inicioInput.addEventListener('change', () => {
  if (problemaInicio() || problemaPeriodo()) inicioInput.value = inicioAnterior;
  atualizarPeriodo();
});
terminoInput.addEventListener('change', () => {
  if (problemaPeriodo()) terminoInput.value = terminoAnterior;
  atualizarPeriodo();
});

function referenciaMes(indice) {
  const [ano, mes] = inicioInput.value.split('-').map(Number);
  const posicao = mes - 1 + indice;
  const anoRef = ano + Math.floor(posicao / 12);
  return `${MESES_ABREV[posicao % 12]}/${String(anoRef).slice(2)}`;
}

function somaPercentuais(servico) {
  return servico.percentuais.reduce((total, valor) => total + (Number(valor) || 0), 0);
}

function atualizarTotal(indiceServico) {
  const celula = cronogramaEl.querySelector(`[data-total="${indiceServico}"]`);
  if (!celula) return;
  const soma = somaPercentuais(servicos[indiceServico]);
  celula.textContent = `${Number(soma.toFixed(2)).toLocaleString('pt-BR')}%`;
  // Verde quando fecha 100%; enquanto isso fica neutro (só é erro se tentar gerar assim).
  celula.className = `cronograma__total${Math.abs(soma - 100) <= 0.01 ? ' cronograma__total--ok' : ''}`;
}

function escapeHtml(texto) {
  return texto.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function renderCronograma() {
  const meses = totalMeses();

  // Ajusta a quantidade de meses de cada serviço, preservando o que já foi digitado.
  servicos.forEach((servico) => {
    servico.percentuais = Array.from({ length: meses }, (_, i) => servico.percentuais[i] ?? '');
  });

  // O botão de adicionar serviço só faz sentido com a tabela montada.
  adicionarServicoWrapper.hidden = meses === 0;

  if (meses === 0) {
    cronogramaEl.innerHTML = problemaPeriodo()
      ? '<p class="cronograma__vazio">Corrija a previsão de início e de término das obras para montar o cronograma.</p>'
      : '<p class="cronograma__vazio">Informe a previsão de início e de término das obras para montar o cronograma.</p>';
    return;
  }

  let trimestres = '';
  for (let inicio = 0; inicio < meses; inicio += 3) {
    const colunas = Math.min(3, meses - inicio);
    trimestres += `<th colspan="${colunas}">${inicio / 3 + 1}º Trimestre</th>`;
  }

  let cabecalhoMeses = '';
  for (let i = 0; i < meses; i += 1) {
    cabecalhoMeses += `<th>${i + 1}º mês<small>${referenciaMes(i)}</small></th>`;
  }

  const linhas = servicos.map((servico, s) => {
    const celulas = servico.percentuais.map((valor, m) => `
      <td><input type="number" min="0" max="100" step="any" inputmode="decimal"
        data-servico="${s}" data-mes="${m}" value="${valor}" aria-label="${escapeHtml(servico.descricao || 'Serviço')} — ${m + 1}º mês (%)"></td>`).join('');
    return `
      <tr>
        <td class="cronograma__servico">
          <input type="text" data-descricao="${s}" value="${escapeHtml(servico.descricao)}" placeholder="Descrição do serviço" aria-label="Serviço ${s + 1}">
        </td>
        ${celulas}
        <td class="cronograma__total" data-total="${s}"></td>
        <td><button type="button" class="btn-remover" data-remover="${s}" aria-label="Remover serviço" title="Remover serviço">&times;</button></td>
      </tr>`;
  }).join('');

  cronogramaEl.innerHTML = `
    <table>
      <thead>
        <tr><th class="cronograma__servico"></th>${trimestres}<th></th><th></th></tr>
        <tr><th class="cronograma__servico">Serviços / Mês</th>${cabecalhoMeses}<th>Total</th><th></th></tr>
      </thead>
      <tbody>${linhas}</tbody>
    </table>`;

  servicos.forEach((_, s) => atualizarTotal(s));
}

cronogramaEl.addEventListener('input', (e) => {
  const { servico, mes, descricao } = e.target.dataset;
  if (descricao !== undefined) {
    servicos[Number(descricao)].descricao = e.target.value;
  } else if (servico !== undefined) {
    const linha = servicos[Number(servico)];
    const anterior = linha.percentuais[Number(mes)];
    // Texto que não é número (ex.: "9-" colado) também não é aceito.
    if (e.target.validity.badInput) {
      e.target.value = anterior;
      return;
    }
    const novo = Number(e.target.value) || 0;
    const somaSemEste = somaPercentuais(linha) - (Number(anterior) || 0);
    // Não aceita valor negativo, acima de 100% ou que faça o serviço passar de 100%.
    if (novo < 0 || novo > 100 || somaSemEste + novo > 100.001) {
      e.target.value = anterior;
      return;
    }
    linha.percentuais[Number(mes)] = e.target.value;
    atualizarTotal(Number(servico));
  }
  clearError('servicos');
});

// Nos percentuais, as teclas de sinal e de expoente não entram.
cronogramaEl.addEventListener('keydown', (e) => {
  if (e.target.dataset.servico !== undefined && ['e', 'E', '+', '-'].includes(e.key)) e.preventDefault();
});

cronogramaEl.addEventListener('click', (e) => {
  const botao = e.target.closest('[data-remover]');
  if (!botao) return;
  servicos.splice(Number(botao.dataset.remover), 1);
  renderCronograma();
});

document.getElementById('btn-adicionar-servico').addEventListener('click', () => {
  servicos.push({ descricao: '', percentuais: [] });
  renderCronograma();
  const novos = cronogramaEl.querySelectorAll('[data-descricao]');
  novos[novos.length - 1]?.focus();
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

// Número no formato brasileiro, formatado enquanto digita: "12500" -> "12.500",
// com vírgula para decimais (até 2 casas).
function formatarNumeroBr(v) {
  const [inteiro, ...decimais] = v.replace(/[^\d,]/g, '').split(',');
  const milhares = inteiro.replace(/^0+(?=\d)/, '').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return decimais.length ? `${milhares},${decimais.join('').slice(0, 2)}` : milhares;
}

function validateEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

const CAMPOS_TEXTO_OBRIGATORIOS = [
  ['nome_empresa', 'Informe o nome da empresa.'],
  ['endereco', 'Informe o endereço.'],
  ['area_empresa', 'Informe a área da empresa.'],
  ['area_construida', 'Informe a área a ser construída.'],
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

  const inicio = inicioInput.value;
  const termino = terminoInput.value;
  if (!inicio) {
    setError('inicio_obras', 'Informe a previsão de início das obras.');
    valid = false;
  } else if (problemaInicio()) {
    setError('inicio_obras', problemaInicio());
    valid = false;
  } else {
    clearError('inicio_obras');
  }
  if (!termino) {
    setError('termino_obras', 'Informe a previsão de término das obras.');
    valid = false;
  } else if (problemaPeriodo()) {
    setError('termino_obras', problemaPeriodo());
    valid = false;
  } else {
    clearError('termino_obras');
  }

  if (totalMeses() > 0) {
    const semDescricao = servicos.some((servico) => !servico.descricao.trim());
    const foraDe100 = servicos.find((servico) => Math.abs(somaPercentuais(servico) - 100) > 0.01);
    if (servicos.length === 0) {
      setError('servicos', 'Adicione ao menos um serviço ao cronograma.');
      valid = false;
    } else if (semDescricao) {
      setError('servicos', 'Informe a descrição de todos os serviços.');
      valid = false;
    } else if (foraDe100) {
      setError('servicos', `Os percentuais de "${foraDe100.descricao}" devem somar 100%.`);
      valid = false;
    } else {
      clearError('servicos');
    }
  }

  // Áreas: só números, maiores que zero; a construída cabe na área da empresa.
  const areaEmpresa = numeroBr(document.getElementById('area_empresa').value);
  const areaConstruida = numeroBr(document.getElementById('area_construida').value);
  [['area_empresa', areaEmpresa], ['area_construida', areaConstruida]].forEach(([id, valor]) => {
    if (!document.getElementById(id).value.trim()) return;
    if (Number.isNaN(valor)) {
      setError(id, 'Informe apenas números (ex.: 12.500 ou 2.500,50).');
      valid = false;
    } else if (valor <= 0) {
      setError(id, 'A área deve ser maior que zero.');
      valid = false;
    }
  });
  if (areaConstruida > areaEmpresa) {
    setError('area_construida', 'A área a ser construída não pode ser maior que a área da empresa.');
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
    nome_empresa: document.getElementById('nome_empresa').value.trim(),
    endereco: document.getElementById('endereco').value.trim(),
    area_empresa: document.getElementById('area_empresa').value.trim(),
    area_construida: document.getElementById('area_construida').value.trim(),
    inicio_obras: inicioInput.value,
    termino_obras: terminoInput.value,
    servicos: servicos.map((servico) => ({
      descricao: servico.descricao.trim(),
      percentuais: servico.percentuais.map((valor) => Number(valor) || 0),
    })),
    g_recaptcha_response: typeof grecaptcha !== 'undefined' ? grecaptcha.getResponse() : '',
  };

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/cadastro/anexo-v-cfo`, {
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
       <p class="feedback__email-status feedback__email-status--warn">Anote o número do protocolo: ele é necessário para enviar o documento assinado.</p>
       <div class="feedback__actions">
         <a class="feedback__link" href="${pdfUrl}" target="_blank" rel="noopener">Baixar documento PDF</a>
         <a class="feedback__link feedback__link--secondary" href="upload-assinado.html?protocolo=${encodeURIComponent(protocolo)}">Já assinei, enviar documento →</a>
       </div>`,
      'success'
    );

    form.reset();
    servicos = SERVICOS_SUGERIDOS.map((descricao) => ({ descricao, percentuais: [] }));
    atualizarPeriodo();
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
restringirCampo(document.getElementById('area_empresa'), formatarNumeroBr);
restringirCampo(document.getElementById('area_construida'), formatarNumeroBr, (v) => {
  // não pode passar da área de referência (quando ela já estiver preenchida)
  const limite = numeroBr(document.getElementById('area_empresa').value);
  return !v || Number.isNaN(limite) || numeroBr(v) <= limite;
});
