from app.config import Settings


def test_settings_defaults():
    # loading settings without an environment file
    settings = Settings(_env_file=None)

    # checking the default application configuration
    assert settings.database_url == "sqlite:///./padel_corpo.db"
    assert settings.secret_key == "dev-secret-key-change-me-in-production"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 1440
    assert settings.allowed_origins == "http://localhost:5173"
    assert settings.upload_dir == "./uploads"
    assert settings.max_upload_size == 2_097_152
    assert settings.max_login_attempts == 5
    assert settings.lockout_minutes == 30


def test_settings_load_environment_overrides(monkeypatch):
    # overriding database and anti-brute-force values
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("MAX_LOGIN_ATTEMPTS", "8")
    monkeypatch.setenv("LOCKOUT_MINUTES", "15")

    # loading settings from the temporary environment
    settings = Settings(_env_file=None)

    # checking that environment values are used
    assert settings.database_url == "sqlite:///./test.db"
    assert settings.max_login_attempts == 8
    assert settings.lockout_minutes == 15


def test_origins_list_splits_trims_and_ignores_empty_entries(monkeypatch):
    # overriding allowed origins with whitespace and empty entries
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        " http://localhost:5173, https://example.com ,,",
    )

    # loading settings from the temporary environment
    settings = Settings(_env_file=None)

    # checking normalized origins
    assert settings.origins_list == [
        "http://localhost:5173",
        "https://example.com",
    ]
