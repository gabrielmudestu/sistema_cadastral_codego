# Publicação no Render (plano grátis)

Alternativa gratuita à VM da CODEGO ([README.md](README.md)). Usa três
serviços gratuitos:

| Parte | Onde | Grátis |
|---|---|---|
| Site + API (backend) | **Render** — um serviço só, `https://<nome>.onrender.com` | sim |
| Banco MySQL | **Aiven** (MySQL gerenciado) | sim — 1 GB |
| E-mail | **Brevo** pela API web | sim — cota diária do plano grátis |

A configuração do Render está no arquivo [`render.yaml`](../render.yaml), na
raiz do projeto.

## O que muda em relação à VM (limitações do plano grátis)

- **O serviço "dorme"** depois de 15 minutos sem acesso. O primeiro acesso
  depois disso leva cerca de 1 minuto. Dá para evitar com um "ping" periódico
  (passo 6).
- **O disco é apagado** a cada reinício ou nova publicação:
  - **PDFs gerados:** quando alguém pede o download de um PDF que não existe
    mais, o sistema **recria o PDF** a partir dos dados do banco, com a data
    original do processo.
  - **PDFs assinados e documentos enviados** (Anexo III, mensagens): não dá para
    recriar. Eles chegam **anexados no e-mail** enviado ao `NOTIFICATION_EMAIL`
    (atualizacaocadastral@) — essa caixa passa a ser o arquivo desses documentos.
    Arquivos grandes demais para o e-mail vão só na lista, e aí se perdem no
    próximo reinício.
- **SMTP é bloqueado** no Render grátis: o e-mail sai pela API do Brevo
  (`EMAIL_PROVIDER=brevo_api`).
- Os dados ficam em empresas de fora (Render, Aiven, Brevo). Para dados pessoais
  (CPF, RG, documentos), confirme com a CODEGO se isso é aceitável.

---

## 1. Banco de dados no Aiven

1. Criar conta em <https://aiven.io> (não pede cartão).
2. **Create service → MySQL → plano Free.**
3. Quando o serviço estiver **Running**, na página dele (*Connection information*)
   anotar: **Host**, **Port**, **User** (`avnadmin`), **Password** e
   **Database name** (`defaultdb`).
4. Baixar o **CA certificate** (botão na mesma página) e abrir o arquivo
   `ca.pem` no Bloco de Notas: o conteúdo inteiro (de
   `-----BEGIN CERTIFICATE-----` até `-----END CERTIFICATE-----`) vai na
   variável `MYSQL_SSL_CA`.

As tabelas são criadas sozinhas quando o backend inicia.

> O Aiven pode desligar serviços grátis que ficarem muito tempo sem uso.

## 2. E-mail no Brevo

1. No painel do Brevo: **SMTP & API → API Keys → Generate a new API key**.
   Copiar a chave (começa com `xkeysib-`) — ela só aparece uma vez.
2. **Senders & IPs → Senders:** o e-mail remetente precisa estar cadastrado e
   verificado.
   - O ideal é um e-mail do domínio da CODEGO (ex.: `naoresponda@codego.com.br`)
     com o domínio autenticado no Brevo (*Senders & IPs → Domains*, o TI
     adiciona os registros DNS).
   - Remetente @gmail.com ou @outlook.com enviado pelo Brevo costuma cair no
     spam (foi o que aconteceu nos testes com `gbmodestos@outlook.com`).

## 3. Criar o serviço no Render

1. Criar conta em <https://render.com> e conectar o GitHub.
   - O repositório é do `gabrielmudestu`: se o Render não listar o
     repositório, o dono precisa autorizar o app do Render nele (no GitHub:
     *Settings → Integrations → GitHub Apps → Render*).
2. **New → Blueprint** → escolher o repositório `sistema_cadastral_codego`,
   branch `main`. O Render lê o `render.yaml` e mostra o serviço
   `sistema-cadastral-codego`.
3. Preencher as variáveis pedidas:

| Variável | Valor |
|---|---|
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | os do Aiven (passo 1) |
| `MYSQL_SSL_CA` | conteúdo do `ca.pem` do Aiven |
| `BREVO_API_KEY` | a chave do Brevo (passo 2) |
| `BREVO_SENDER_EMAIL` | o remetente verificado no Brevo |
| `RECAPTCHA_SECRET_KEY` | deixar vazio por enquanto (passo 5) |

   As demais já vêm do `render.yaml` (`EMAIL_PROVIDER=brevo_api`,
   `NOTIFICATION_EMAIL=atualizacaocadastral@codego.com.br`,
   `SERVIR_FRONTEND=true`, `APP_ENV=production` etc.).
4. **Apply.** A primeira publicação leva alguns minutos (monta a imagem com
   o gerador de PDF). O endereço aparece no topo da página do serviço, ex.:
   `https://sistema-cadastral-codego.onrender.com`.

Depois disso, **cada push na `main` publica sozinho** (`autoDeploy`). Lembre
que cada publicação apaga o disco (ver limitações).

## 4. Testar

1. Abrir o endereço do Render: deve aparecer a tela inicial.
2. `https://<endereço>/health` deve responder `{"status":"ok"}`.
3. Fazer o ciclo completo com um e-mail seu no formulário: gerar o PDF →
   receber o e-mail com o protocolo → enviar o assinado → ver o recibo →
   enviar uma mensagem. Os avisos vão para o `NOTIFICATION_EMAIL`.
4. Se algo falhar: página do serviço no Render → **Logs**.

## 5. reCAPTCHA

Quem administra a chave do reCAPTCHA (a `data-sitekey` dos formulários) deve,
em <https://www.google.com/recaptcha/admin>, adicionar o domínio do Render
(ex.: `sistema-cadastral-codego.onrender.com`). Depois, no Render
(*Environment*): `RECAPTCHA_SECRET_KEY` = chave secreta e
`RECAPTCHA_ENABLED=true`.

Enquanto estiver desligado, os formulários ficam sem proteção contra envios
automáticos (spam).

## 6. Evitar que o serviço durma (opcional)

O plano grátis dá 750 horas por mês — o suficiente para **um** serviço ficar
ligado o mês todo. Um monitor gratuito (ex.: <https://uptimerobot.com>) que
acessa `https://<endereço>/health` a cada 10 minutos mantém o serviço
acordado: o site responde sempre rápido e o disco só é apagado nas
publicações e reinícios, não a cada 15 minutos parado.

## 7. Netlify

Com o site servido pelo próprio Render, o Netlify deixa de ser necessário.
Se quiser mantê-lo, preencha `API_PRODUCAO` em `frontend/js/config.js` com o
endereço do Render e defina `CORS_ORIGINS=https://codegobr.netlify.app` no
Render.
