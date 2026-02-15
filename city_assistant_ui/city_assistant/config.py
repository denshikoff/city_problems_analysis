from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent  # корень проекта


@dataclass(frozen=True)
class AppConfig:
    artifacts_root: Path = BASE_DIR / os.getenv("ARTIFACTS_ROOT", "artifacts")

    scenario_id: str = os.getenv("SCENARIO_ID", "s1_base")

    problems_csv: str = os.getenv("PROBLEMS_CSV", "problems_with_complexity.csv")
    agent_payload_json: str = os.getenv("AGENT_PAYLOAD_JSON", "agent_payload.json")
    agent_report_json: str = os.getenv("AGENT_REPORT_JSON", "final_agent_report.json")

    chat_mode: str = os.getenv("CHAT_MODE", "heuristic")
    top_k_ctx_default: int = int(os.getenv("TOP_K_CTX", "10"))
