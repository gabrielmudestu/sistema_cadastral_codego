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
│   ├── Dockerfile
│   └── docker-compose.yml
└── docs/                 # Documentação complementar do projeto
```

## Entidades do banco de dados

- **usuarios** — Nome, CPF/CNPJ, E-mail, Telefone, Cargo, Data de Criação
- **processos_documentos** — protocolo, caminhos dos PDFs (preenchido/assinado), status (Pendente, Assinado, Cancelado), texto do recibo, timestamps
- **mensagens** — remetente, assunto, conteúdo, vínculo opcional com processo
- **anexos_mensagem** — nome original, caminho no storage, tamanho em bytes, tipo MIME

## Setup local

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
```

A API ficará disponível em `http://localhost:8000` e o front-end estático em `http://localhost:8080` (ajustar conforme configuração final do compose).

## Convenção de branches

- `main` — versão estável
- `dev` — integração de features
- `feature/<nome-da-feature>` — desenvolvimento de novas funcionalidades

## Roadmap

O planejamento completo de tarefas está no quadro Trello **Sistema Cadastral CODEGO**.
