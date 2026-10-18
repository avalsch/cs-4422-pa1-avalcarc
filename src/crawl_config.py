from dataclasses import dataclass
from pathlib import Path

DEFAULT_USER_AGENT = "KSU CS4422-Crawler/1.0"
DEFAULT_DELAY = 1.0
DEFAULT_BUDGET = 500
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_MAX_REDIRECT = 10
DEFAULT_TIMEOUT = 30.0


@dataclass
class Config:
    seeds: list[str]
    budget: int
    delay: float
    output_dir: Path
    user_agent: str = DEFAULT_USER_AGENT
    max_bytes: int = DEFAULT_MAX_BYTES
    max_redirects: int = DEFAULT_MAX_REDIRECT
    timeout: float = DEFAULT_TIMEOUT
    checkpoint_path: Path | None = None
    random_seed: int | None = None
