import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, wait_for_db
from app.routers import cadastro, upload, recibo, mensagens, processos

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
)

# Espera o MySQL estar realmente pronto (evita crash na corrida de
# inicialização do container) e cria as tabelas caso ainda não existam
# (em produção, prefira gerenciar via Alembic/migrations)
wait_for_db()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema Cadastral CODEGO",
    description="API para cadastro, geração de documentos, upload assinado, recibo eletrônico e mensagens.",
    version="0.1.0",
    # Documentação interativa (/docs) só fora de produção.
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    # CORS_ORIGINS no .env: "*" (padrão) ou os endereços do site separados por
    # vírgula. Com o site e a API no mesmo endereço (deploy/ com Caddy), o CORS
    # nem é usado; só importa se o site ficar em outro lugar (ex.: Netlify).
    allow_origins=[origem.strip() for origem in settings.cors_origins.split(",") if origem.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(cadastro.router, prefix="/api/cadastro", tags=["Cadastro"])
app.include_router(upload.router, prefix="/api/cadastro", tags=["Upload"])
app.include_router(recibo.router, prefix="/api/recibo", tags=["Recibo"])
app.include_router(mensagens.router, prefix="/api/mensagens", tags=["Mensagens"])
app.include_router(processos.router, prefix="/api/processos", tags=["Processos"])

# Site servido pelo próprio backend (SERVIR_FRONTEND=true, ex.: no Render). Fica
# por último para as rotas da API e o /health terem prioridade.
if settings.servir_frontend and os.path.isdir(settings.frontend_dir):
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
