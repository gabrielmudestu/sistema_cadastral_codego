// Endereço da API (backend) usado por todas as páginas do site.
// Carregar antes dos outros scripts da página.
//
// - Desenvolvimento (docker-compose.yml: site na porta 8080, API na 8000, ou
//   arquivo aberto direto): http://<mesma máquina>:8000.
// - Site e API em lugares diferentes (ex.: site no Netlify, backend na VM):
//   preencher API_PRODUCAO com o endereço https do backend.
// - Produção na VM (deploy/): o Caddy serve o site e encaminha /api para o
//   backend no mesmo endereço, então a API é o próprio endereço do site.
(function () {
  const API_PRODUCAO = '';

  const { protocol, hostname, port, origin } = window.location;

  if (protocol === 'file:' || port === '8080') {
    window.CODEGO_API_BASE_URL = `http://${hostname || 'localhost'}:8000`;
  } else if (API_PRODUCAO) {
    window.CODEGO_API_BASE_URL = API_PRODUCAO.replace(/\/+$/, '');
  } else {
    window.CODEGO_API_BASE_URL = origin;
  }
})();
