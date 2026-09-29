// Endereço da API (backend) usado por todas as páginas do site.
// Carregar antes dos outros scripts da página.
//
// - Rodando no computador (localhost, 127.0.0.1 ou IP da rede local): usa o
//   backend do Docker na porta 8000 da mesma máquina.
// - Publicado (Netlify ou outro domínio): usa API_PRODUCAO.
//
// Quando o backend estiver publicado, é só preencher API_PRODUCAO com o
// endereço dele (https), ex.: 'https://api.sistemacadastral.codego.com.br'.
(function () {
  const API_PRODUCAO = '';

  const host = window.location.hostname;
  const rodandoLocal =
    host === '' || // arquivo aberto direto (file://)
    host === 'localhost' ||
    /^127\./.test(host) ||
    /^10\./.test(host) ||
    /^192\.168\./.test(host) ||
    /^172\.(1[6-9]|2\d|3[01])\./.test(host);

  if (rodandoLocal) {
    window.CODEGO_API_BASE_URL = `http://${host || 'localhost'}:8000`;
  } else if (API_PRODUCAO) {
    window.CODEGO_API_BASE_URL = API_PRODUCAO.replace(/\/+$/, '');
  } else {
    // Publicado mas sem API_PRODUCAO preenchido: o backend ainda não está no ar.
    window.CODEGO_API_BASE_URL = 'http://localhost:8000';
    console.warn('config.js: API_PRODUCAO não definido; o site publicado não vai encontrar o backend.');
  }
})();
