import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
# The API and worker load the same file, regardless of their working directory.
# Explicit process environment values still take precedence.
load_dotenv(ROOT / 'assessment_service' / '.env')


def state_directory():
    path = Path(os.getenv('KGH_STATE_DIR', str(ROOT / 'var' / 'assessments')))
    return (path if path.is_absolute() else ROOT / path).resolve()


@dataclass
class Settings:
    state_dir: Path = field(default_factory=state_directory)
    public_url: str = field(default_factory=lambda: os.getenv('KGH_PUBLIC_URL', 'http://localhost:8000').rstrip('/'))
    cors_origins: list[str] = field(default_factory=lambda: [origin.strip() for origin in os.getenv('KGH_CORS_ORIGINS', '').split(',') if origin.strip()])
    submissions_per_day: int = field(default_factory=lambda: int(os.getenv('KGH_SUBMISSIONS_PER_DAY', '3')))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv('KGH_TIMEOUT_SECONDS', '3600')))
    max_dump_bytes: int = field(default_factory=lambda: int(os.getenv('KGH_MAX_DUMP_BYTES', str(1024**3))))
    memory_bytes: int = field(default_factory=lambda: int(os.getenv('KGH_MEMORY_BYTES', str(4 * 1024**3))))
    disk_bytes: int = field(default_factory=lambda: int(os.getenv('KGH_DISK_BYTES', str(2 * 1024**3))))
    triple_limit: int = field(default_factory=lambda: int(os.getenv('KGH_TRIPLE_LIMIT', '1000000')))

    def __post_init__(self):
        for name in ('submissions_per_day', 'timeout_seconds', 'max_dump_bytes', 'memory_bytes', 'disk_bytes', 'triple_limit'):
            if getattr(self, name) <= 0:
                raise ValueError(f'{name} must be positive')
        self.state_dir = Path(self.state_dir).resolve()
