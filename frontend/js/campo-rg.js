// RG do representante em campos separados — número, órgão emissor e UF — que
// são juntados num texto só antes do envio, no mesmo formato de sempre
// ("4.567.890 SSP-GO"). Assim o backend e o PDF não mudam.
// Usado pelos formulários que pedem RG; carregar antes do script da página.

const ORGAOS_EMISSORES_RG = [
  ['SSP', 'Secretaria de Segurança Pública'],
  ['PC', 'Polícia Civil'],
  ['DETRAN', 'Departamento Estadual de Trânsito'],
  ['IFP', 'Instituto Félix Pacheco'],
  ['IGP', 'Instituto-Geral de Perícias'],
  ['IIRGD', 'Instituto de Identificação Ricardo Gumbleton Daunt'],
  ['SDS', 'Secretaria de Defesa Social'],
  ['SESP', 'Secretaria de Estado da Segurança Pública'],
  ['SEJUSP', 'Secretaria de Justiça e Segurança Pública'],
  ['SJS', 'Secretaria da Justiça e Segurança'],
  ['PM', 'Polícia Militar'],
  ['CBM', 'Corpo de Bombeiros Militar'],
  ['MB', 'Marinha do Brasil'],
  ['EB', 'Exército Brasileiro'],
  ['FAB', 'Força Aérea Brasileira'],
];

const UFS_RG = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA',
  'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

// Número do RG: números, pontos, hífen e X (dígito verificador em SP/RJ);
// no máximo 14 números (o que passar disso, inclusive ao colar, é cortado).
function formatarNumeroRg(v) {
  let numeros = 0;
  return [...v.toUpperCase().replace(/[^\dX.-]/g, '')]
    .filter((c) => !/\d/.test(c) || (numeros += 1) <= 14)
    .join('');
}

function orgaoEmissorRg() {
  const orgao = document.getElementById('representante_rg_orgao').value;
  if (orgao !== 'OUTRO') return orgao;
  return document.getElementById('representante_rg_orgao_outro').value.trim();
}

// Texto enviado ao backend, ex.: "4.567.890 SSP-GO".
function montarRg() {
  const numero = document.getElementById('representante_rg').value.trim();
  const uf = document.getElementById('representante_rg_uf').value;
  return `${numero} ${orgaoEmissorRg()}-${uf}`;
}

// Órgão "Outro" escolhido sem dizer qual (órgão e UF vazios são tratados na
// lista de campos obrigatórios de cada formulário).
function validarOrgaoOutroRg() {
  const orgao = document.getElementById('representante_rg_orgao').value;
  if (orgao === 'OUTRO' && !orgaoEmissorRg()) {
    setError('representante_rg_orgao_outro', 'Informe qual é o órgão emissor.');
    return false;
  }
  clearError('representante_rg_orgao_outro');
  return true;
}

(function iniciarCampoRg() {
  const orgaoEl = document.getElementById('representante_rg_orgao');
  const ufEl = document.getElementById('representante_rg_uf');
  const outroEl = document.getElementById('representante_rg_orgao_outro');
  if (!orgaoEl || !ufEl || !outroEl) return;

  orgaoEl.innerHTML =
    '<option value="" disabled selected>Selecione</option>' +
    ORGAOS_EMISSORES_RG.map(([sigla, nome]) => `<option value="${sigla}">${sigla} — ${nome}</option>`).join('') +
    '<option value="OUTRO">Outro</option>';
  ufEl.innerHTML =
    '<option value="" disabled selected>Selecione</option>' +
    UFS_RG.map((uf) => `<option value="${uf}">${uf}</option>`).join('');

  const campoOutro = outroEl.closest('.field');
  orgaoEl.addEventListener('change', () => {
    campoOutro.hidden = orgaoEl.value !== 'OUTRO';
    if (!campoOutro.hidden) outroEl.focus();
  });
  // Sigla do órgão: só letras, em maiúsculas.
  outroEl.addEventListener('input', () => {
    outroEl.value = outroEl.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 10);
  });
})();
