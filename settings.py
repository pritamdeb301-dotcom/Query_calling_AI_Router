from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # We make these optional so the app doesn't crash if one is temporarily missing
    vapi_api_key: str | None = None
    openrouter_api_key: str | None = None 
    
    database_url: str = "sqlite:///appointments.db"
    chroma_db_path: str = "./vectorstore.db"
    debug: bool = True
    port: int = 8000

    # This is the correct Pydantic V2 configuration syntax
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # This safely ignores any other random keys on your Mac
    )