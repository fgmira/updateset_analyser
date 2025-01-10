from pydantic import (
    Field,
    SecretStr,
    AmqpDsn,
    AnyUrl,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UPDATESET_ANALYSER_",
        env_file=".env",
    )
    SERVICE_NOW_USER: str = Field(
        ...,
        description="The username to authenticate with the ServiceNow API",
    )
    SERVICE_NOW_PASSWORD: SecretStr = Field(
        ...,
        description="The password to authenticate with the ServiceNow API",
    )
    SERVICE_NOW_URL: AnyUrl = Field(
        ...,
        description="The base URL of the ServiceNow API",
    )
    CELERY_BROKER_HOST: str = Field(
        ...,
        description="The HOST of the Celery broker",
    )
    CELERY_BROKER_PORT: int = Field(
        ...,
        description="The PORT of the Celery broker",
    )
    CELERY_BROKER_USER: str = Field(
        ...,
        description="The username to authenticate with the Celery broker",
    )
    CELERY_BROKER_PASSWORD: SecretStr = Field(
        ...,
        description="The password to authenticate with the Celery broker",
    )
    OPENAI_API_KEY: SecretStr = Field(
        ...,
        description="The API key to authenticate with the OpenAI API",
    )
    REDIS_HOST: str = Field(
        ...,
        description="The HOST of the Redis broker",
    )
    REDIS_PORT: int = Field(
        ...,
        description="The PORT of the Redis broker",
    )


app_settings = AppSettings()  # type: ignore
