from dataclasses import dataclass
from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parent.parent
# если config.py лежит в city_assistant/, то parent.parent = city_assistant_ui/

@dataclass(frozen=True)
class AppConfig:
    artifacts_root: Path = Path(os.getenv("ARTIFACTS_ROOT", str(APP_DIR / "artifacts")))
    scenario_id: str = os.getenv("SCENARIO_ID", "s1_base")

    problems_csv: str = os.getenv("PROBLEMS_CSV", "problems_with_complexity.csv")
    agent_report_json: str = os.getenv("AGENT_REPORT_JSON", "final_agent_report.json")
