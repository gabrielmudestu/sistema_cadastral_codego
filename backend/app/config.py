from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mysql_host: str = "db"
    mysql_port: int = 3306
    mysql_database: str = "sistema_cadastral_codego"
    mysql_user: str = "codego_app"
    mysql_password: str = "change_me"

    app_env: str = "development"
    app_secret_key: str = "change_me_secret"

    upload_dir: str = "/app/storage/uploads"
    signed_dir: str = "/app/storage/signed"
    max_upload_size_mb: int = 10

    protocol_prefix: str = "REC"

    # E-mail (SMTP) — padrão configurado para Outlook/Office365
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Sistema Cadastral CODEGO"
    smtp_enabled: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


settings = Settings()
