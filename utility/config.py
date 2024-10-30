
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    """ DC Bot Configuration """

    discord_token: str
    discord_prefix: str = '!'
    discord_test_guild_id: int = 0

    """ AnythingLLM API Configuration """
    anythingllm_host: str
    anythingllm_api_key: str
    anythingllm_workspace_slug: str = 'default'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

config = Config()