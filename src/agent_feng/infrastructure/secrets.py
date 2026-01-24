import os

from agent_feng.core.abc import SecretsProvider


class EnvironmentVariableSecretsProvider(SecretsProvider):
    """Secrets provider that reads from environment variables."""

    _secrets_prefix: str = "SECRET__"

    def get_secret(self, secret_name: str, default_value: str | None = None) -> str:
        """Retrieve secret from environment variables."""
        secret_name = (
            EnvironmentVariableSecretsProvider._secrets_prefix + secret_name.upper()
        )
        value = os.getenv(secret_name, default_value)
        if value is None:
            raise KeyError(f"Secret not found: {secret_name}")
        return value
