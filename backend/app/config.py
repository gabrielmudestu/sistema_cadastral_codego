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

    # E-mail fixo da empresa que recebe a cópia de TODOS os documentos assinados
    # (em vez do e-mail que a pessoa preencheu no cadastro)
    notification_email: str = ""

    # E-mail — provider "smtp" (Gmail etc.) ou "outlook_graph" (Microsoft Graph, para Outlook/Hotmail)
    email_provider: str = "smtp"

    # E-mail (SMTP) — usado quando email_provider="smtp"
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""  # e-mail do remetente (precisa estar verificado no provedor, ex: Brevo). Se vazio, usa smtp_user.
    smtp_from_name: str = "Sistema Cadastral CODEGO"
    smtp_enabled: bool = False

    # Outlook via Microsoft Graph (OAuth2) — usado quando email_provider="outlook_graph"
    outlook_client_id: str = ""
    outlook_tenant: str = "consumers"  # "consumers" para contas pessoais (@outlook.com, @hotmail.com)
    outlook_sender_email: str = ""  # o e-mail da conta autorizada no login único (device code flow)
    outlook_token_cache_path: str = "/app/storage/outlook_token_cache.bin"

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
