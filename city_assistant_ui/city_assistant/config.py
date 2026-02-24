from dataclasses import dataclass
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # /opt/render/project/src
UI_ARTIFACTS = PROJECT_ROOT / "city_assistant_ui" / "artifacts"
FALLBACK_ARTIFACTS = PROJECT_ROOT / "artifacts"

def _default_artifacts_root() -> Path:
    # 1) если явно задано — используем
    env = os.getenv("ARTIFACTS_ROOT")
    if env:
        return Path(env)

    # 2) auto-detect (как у тебя на Render)
    if UI_ARTIFACTS.exists():
        return UI_ARTIFACTS

    # 3) fallback
    return FALLBACK_ARTIFACTS

@dataclass(frozen=True)
class AppConfig:
    artifacts_root: Path = _default_artifacts_root()
    scenario_id: str = os.getenv("SCENARIO_ID", "s1_base")

    problems_csv: str = os.getenv("PROBLEMS_CSV", "problems_with_complexity.csv")
    agent_report_json: str = os.getenv("AGENT_REPORT_JSON", "final_agent_report.json")
    chat_mode: str = os.getenv("CHAT_MODE", "heuristic")
    top_k_ctx_default: int = int(os.getenv("TOP_K_CTX", "10"))