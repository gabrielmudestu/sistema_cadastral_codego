from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import cadastro, upload, recibo, mensagens, processos

# Cria as tabelas automaticamente caso ainda não existam
# (em produção, prefira gerenciar via Alembic/migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema Cadastral CODEGO",
    description="API para cadastro, geração de documentos, upload assinado, recibo eletrônico e mensagens.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar para o domínio do front em produção
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
