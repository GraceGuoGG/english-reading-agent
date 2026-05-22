from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_encrypt_key: str = ""

    bitable_app_token: str = ""
    bitable_wordbook_table_id: str = ""
    bitable_reading_table_id: str = ""
    bitable_config_table_id: str = ""

    doubao_api_key: str = ""
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    doubao_model: str = ""

    github_rss_feeds: str = "https://github.blog/feed/,https://github.blog/engineering/feed/"

    push_time: str = "07:30"
    daily_short_count: int = 1
    daily_medium_count: int = 1

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def rss_feed_list(self) -> list[str]:
        return [f.strip() for f in self.github_rss_feeds.split(",") if f.strip()]


settings = Settings()
