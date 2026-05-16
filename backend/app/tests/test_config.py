from __future__ import annotations

import pytest

from app.core.config import Settings


def test_settings_reads_environment_and_casts_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in {
        "APP_NAME": "Test App",
        "PORT": "9000",
        "DB_PORT": "15432",
        "DB_HEALTHCHECK_RETRIES": "9",
    }.items():
        monkeypatch.setenv(key, value)

    settings = Settings()

    assert settings.app_name == "Test App"
    assert settings.port == 9000
    assert settings.db_port == 15432
    assert settings.db_healthcheck_retries == 9
