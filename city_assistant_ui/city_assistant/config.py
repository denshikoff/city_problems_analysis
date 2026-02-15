from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    # корень артефактов
    artifacts_root: str = os.getenv("ARTIFACTS_ROOT", "artifacts")

    # сценарий по умолчанию
    scenario_id: str = os.getenv("SCENARIO_ID", "s1_base")

    # файлы внутри сценария
    problems_csv: str = os.getenv("PROBLEMS_CSV", "problems_with_complexity.csv")
    agent_payload_json: str = os.getenv("AGENT_PAYLOAD_JSON", "agent_payload.json")
    agent_report_json: str = os.getenv("AGENT_REPORT_JSON", "final_agent_report.json")

    chat_mode: str = os.getenv("CHAT_MODE", "heuristic")  # heuristic | llm
    top_k_ctx_default: int = int(os.getenv("TOP_K_CTX", "10"))
