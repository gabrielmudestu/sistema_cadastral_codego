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
