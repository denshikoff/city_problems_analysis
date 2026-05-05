from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
class DataRepository:
    def __init__(self, artifacts_root, scenario_id="default"):
        self.artifacts_root=Path(artifacts_root); self.scenario_id=scenario_id; self.scenario_dir=self.artifacts_root/scenario_id
    def list_scenarios(self): return sorted([p.name for p in self.artifacts_root.iterdir() if p.is_dir()]) if self.artifacts_root.exists() else []
    def path(self, rel):
        p=Path(rel); return p if p.is_absolute() else self.scenario_dir/p
    @staticmethod
    def _read_jsonl(path):
        rows=[]
        with path.open("r",encoding="utf-8") as f:
            for line in f:
                if line.strip(): rows.append(json.loads(line))
        return rows
    def load_candidates(self,jsonl_relative,csv_relative:Optional[str]=None):
        jp=self.path(jsonl_relative)
        if jp.exists(): return self._read_jsonl(jp)
        if csv_relative and self.path(csv_relative).exists():
            df=pd.read_csv(self.path(csv_relative)); return [self._flat(r) for _,r in df.iterrows()]
        return []
    @staticmethod
    def _flat(r):
        def split(v): return [] if pd.isna(v) else [x.strip() for x in str(v).split(';') if x.strip()]
        return {"candidate_id":r.get("candidate_id"),"title":r.get("Проблема"),"problem_type":r.get("Тип_проблемы"),"complexity_score":float(r.get("Complexity_score",0) or 0),"metrics":{"frequency":int(r.get("Частота_упоминаний",0) or 0),"relations_count":int(r.get("Количество_связей",0) or 0),"subgraph_density":float(r.get("Плотность_подграфа",0) or 0)},"entities":split(r.get("Ключевые_сущности")),"actions":split(r.get("Действия")),"problem_anchors":split(r.get("Проблемные_признаки")),"territories":split(r.get("Территории")),"evidence_appeals":[]}
