# Sistema Cadastral CODEGO

Sistema para automação de coleta de dados cadastrais, geração de documentos em PDF para assinatura, recebimento do arquivo assinado (reenvio), emissão de recibo eletrônico com protocolo único, e módulo de mensagens/anexos complementares.

Baseado na especificação do protótipo funcional e no modelo de documento **Anexo VIII-D — Formulário para Solicitações Diversas** (Regulamento de Alienação de Áreas, CODEGO).

## Stack

- **Front-end:** HTML + CSS puro
- **Back-end:** Python (FastAPI)
- **Banco de Dados:** MySQL
- **Infraestrutura:** Docker Compose

## Fluxo da aplicação

1. **Preenchimento e Geração** — usuário preenche o formulário cadastral e o sistema gera o PDF preenchido para download.
2. **Assinatura e Reenvio** — usuário assina o PDF (digital ou manualmente) e reenvia o arquivo assinado.
3. **Validação e Recibo Eletrônico** — sistema valida o recebimento, armazena o documento e gera o recibo com número de protocolo, data/hora e declaração de recebimento.
4. **Módulo de Mensagem e Anexos** — envio de mensagens com identificação do remetente e anexos complementares (comprovantes, fotos, outros PDFs).

## Estrutura do projeto

```
sistema_cadastral_codego/
├── backend/
│   └── app/
│       ├── routers/      # Endpoints da API (cadastro, upload, recibo, mensagens)
│       ├── models/       # Modelos ORM (SQLAlchemy)
│       ├── schemas/      # Schemas Pydantic
│       ├── services/     # Regras de negócio (geração de PDF, protocolo, etc.)
│       └── templates/    # Templates usados na geração do PDF
├── frontend/
│   ├── css/
│   ├── js/
│   └── assets/
├── database/
│   └── migrations/       # Scripts de schema/migração MySQL
├── docker/
│   └── Dockerfile
├── docker-compose.yml
└── docs/                 # Documentação complementar do projeto
```

## Entidades do banco de dados

- **usuarios** — Nome, CPF/CNPJ, E-mail, Telefone, Cargo, Data de Criação
- **processos_documentos** — protocolo, caminhos dos PDFs (preenchido/assinado), status (Pendente, Assinado, Cancelado), texto do recibo, timestamps
- **mensagens** — remetente, assunto, conteúdo, vínculo opcional com processo
- **anexos_mensagem** — nome original, caminho no storage, tamanho em bytes, tipo MIME

## Envio de e-mail

O sistema envia uma confirmação por e-mail (com o PDF assinado em anexo) quando
o documento assinado é recebido (Tela 2). Dois provedores são suportados,
configurados via `EMAIL_PROVIDER` no `.env`:

### Opção A — SMTP (Gmail, etc.)

Simples: usuário + senha de app. Não funciona mais com contas Outlook/Hotmail
pessoais (veja Opção B). No `.env`:

```
EMAIL_PROVIDER=smtp
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app_de_16_caracteres
```

Requer verificação em duas etapas ativada na conta Google, com uma senha de
app gerada em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

### Opção B — Outlook/Hotmail (Microsoft Graph API)

A Microsoft desativou a autenticação básica (usuário+senha, incluindo senhas
de app) por SMTP para contas pessoais @outlook.com/@hotmail.com. Para usar uma
conta Outlook, o sistema envia pela Microsoft Graph API com OAuth2:

1. **Cadastre um app no Azure** (gratuito, usa a mesma conta Microsoft que vai
   enviar os e-mails):
   - Acesse [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID**
     → **Registros de aplicativo** → **Novo registro**
   - Nome: `Sistema Cadastral CODEGO` (ou o que preferir)
   - Tipos de conta compatíveis: **Contas somente em qualquer diretório
     organizacional e contas pessoais da Microsoft**
   - Não precisa de URI de redirecionamento
   - Depois de criado, copie o **Application (client) ID** da página "Visão geral"
   - Vá em **Autenticação** → ative **"Allow public client flows"** → Salvar
   - Vá em **Permissões de API** → **Adicionar uma permissão** → **Microsoft
     Graph** → **Permissões delegadas** → busque e marque **Mail.Send** →
     Adicionar permissões

2. **Configure o `.env`:**
   ```
   EMAIL_PROVIDER=outlook_graph
   OUTLOOK_CLIENT_ID=<o Application (client) ID copiado acima>
   OUTLOOK_TENANT=consumers
   ```

3. **Faça o login único** (autoriza o sistema a enviar como sua conta):
   ```
   docker compose exec backend python scripts/setup_outlook_auth.py
   ```
   Isso mostra um código e um link. Abra o link em qualquer navegador, digite
   o código, faça login com a conta Outlook que vai enviar os e-mails, e
   autorize. O token fica salvo em disco (persistido no volume Docker) e é
   renovado automaticamente — não precisa logar de novo, a menos que o token
   seja revogado.

4. Reinicie o backend: `docker compose restart backend`

## Deploy do front-end no Netlify

O `netlify.toml` na raiz já configura o Netlify para publicar a pasta
`frontend/` (não precisa mover nenhum arquivo nem mexer nas configurações
manuais do painel — funciona automaticamente com o site conectado ao GitHub).

**Importante:** o Netlify só hospeda o front-end (arquivos estáticos). O
back-end (FastAPI) continua precisando rodar em outro lugar (seu Docker local,
ou um serviço como Render/Railway/EC2). Depois de hospedar o back-end em algum
endereço público, aponte o front-end pra ele definindo `window.CODEGO_API_BASE_URL`
antes do `js/anexo-viii-d.js` carregar — por exemplo, adicionando isto no
`<head>` de cada página HTML:

```html
<script>window.CODEGO_API_BASE_URL = 'https://sua-api-em-producao.com';</script>
```

Sem isso, o front-end publicado no Netlify vai tentar falar com
`http://localhost:8000` (o padrão), que não existe fora da sua máquina.

## Setup local

```bash
cp .env.example .env
docker compose up --build
```

A API ficará disponível em `http://localhost:8000` e o front-end estático em `http://localhost:8080` (ajustar conforme configuração final do compose).

## Convenção de branches

- `main` — versão estável
- `dev` — integração de features
- `feature/<nome-da-feature>` — desenvolvimento de novas funcionalidades

## Roadmap

O planejamento completo de tarefas está no quadro Trello **Sistema Cadastral CODEGO**.
