import json
import os
import pandas as pd

REQUIRED_COLS = [
    "Проблема",
    "Тип_проблемы",
    "Частота_упоминаний",
    "Количество_субъектов",
    "Количество_действий",
    "Плотность_подграфа",
    "Complexity_score",
]


class DataRepository:
    def __init__(self, artifacts_root: str, scenario_id: str):
        self.artifacts_root = artifacts_root
        self.scenario_id = scenario_id

    def scenario_dir(self) -> str:
        return os.path.join(self.artifacts_root, self.scenario_id)

    def path(self, filename: str) -> str:
        return os.path.join(self.scenario_dir(), filename)

    def list_scenarios(self) -> list[str]:
        if not os.path.isdir(self.artifacts_root):
            return []
        return sorted([d for d in os.listdir(self.artifacts_root) if os.path.isdir(os.path.join(self.artifacts_root, d))])

    def load_problems(self, filename: str) -> pd.DataFrame:
        path = filename if os.path.isabs(filename) else self.path(filename)
    
        df = pd.read_csv(path)

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"В CSV не хватает колонок: {missing}. Найдены: {list(df.columns)}")

        df["Complexity_score"] = pd.to_numeric(df["Complexity_score"], errors="coerce").fillna(0.0)
        df["Частота_упоминаний"] = pd.to_numeric(df["Частота_упоминаний"], errors="coerce").fillna(0).astype(int)
        df["Количество_субъектов"] = pd.to_numeric(df["Количество_субъектов"], errors="coerce").fillna(0).astype(int)
        df["Количество_действий"] = pd.to_numeric(df["Количество_действий"], errors="coerce").fillna(0).astype(int)
        df["Плотность_подграфа"] = pd.to_numeric(df["Плотность_подграфа"], errors="coerce").fillna(0.0)

        df["Проблема"] = df["Проблема"].astype(str).str.strip()
        df["Тип_проблемы"] = df["Тип_проблемы"].astype(str).str.strip()
        return df

    def load_json(self, filename: str) -> dict | None:
        path = filename if os.path.isabs(filename) else self.path(filename)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
