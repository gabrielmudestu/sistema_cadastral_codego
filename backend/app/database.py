import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries: int = 30, delay_seconds: float = 2.0) -> None:
    """
    Espera o MySQL ficar pronto para conexões antes de seguir.

    Necessário porque, durante a inicialização, o container do MySQL sobe
    um servidor temporário (só para rodar os scripts de schema em
    /docker-entrypoint-initdb.d) que responde normalmente ao healthcheck
    do Docker e depois se desliga para iniciar o servidor definitivo.
    Nesse intervalo, uma tentativa de conexão no momento errado falha
    mesmo com o container já marcado como "healthy".
    """
    ultimo_erro: Exception | None = None
    for tentativa in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as erro:
            ultimo_erro = erro
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Não foi possível conectar ao banco de dados após {max_retries} tentativas."
    ) from ultimo_erro
