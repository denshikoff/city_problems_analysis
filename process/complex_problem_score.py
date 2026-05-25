from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import math

@dataclass(frozen=True)
class CalibrationConfig:
    scale_frequency: float = 120.0
    scale_unique_entities: float = 60.0
    scale_unique_actions: float = 40.0
    scale_relations_count: float = 120.0
    density_min: float = 0.01
    density_max: float = 0.40
    min_actions_for_systemic: int = 2
    min_entities_for_systemic: int = 3
    penalty_if_too_simple: float = 0.15

class ComplexProblemScorer:
    """Индекс комплексности кандидата проблемы. LLM его не пересчитывает."""
    def __init__(self, frequency:int, unique_entities:int, unique_actions:int,
                 subgraph_density:float, relations_count:int,
                 weights:Dict[str,float]|None=None, calibration:CalibrationConfig|None=None):
        self.frequency=max(0,int(frequency or 0)); self.unique_entities=max(0,int(unique_entities or 0))
        self.unique_actions=max(0,int(unique_actions or 0)); self.subgraph_density=float(subgraph_density or 0)
        self.relations_count=max(0,int(relations_count or 0)); self.cal=calibration or CalibrationConfig()
        self.w=weights or {"frequency":0.30,"entities":0.25,"actions":0.15,"density":0.15,"relations":0.15}
        s=sum(self.w.values()); self.w={k:v/s for k,v in self.w.items()}
    @staticmethod
    def _clamp(x:float, lo=0.0, hi=1.0)->float: return max(lo,min(hi,float(x)))
    @staticmethod
    def _soft(value:float, scale:float)->float: return 0.0 if scale<=0 else 1.0-math.exp(-max(0.0,float(value))/scale)
    def _density(self)->float:
        d=self._clamp(self.subgraph_density); a,b=self.cal.density_min,self.cal.density_max
        return 0.0 if b<=a else self._clamp((d-a)/(b-a))
    def _components(self)->Dict[str,float]:
        return {"frequency_component":self._soft(self.frequency,self.cal.scale_frequency),
                "entities_component":self._soft(self.unique_entities,self.cal.scale_unique_entities),
                "actions_component":self._soft(self.unique_actions,self.cal.scale_unique_actions),
                "relations_component":self._soft(self.relations_count,self.cal.scale_relations_count),
                "density_component":self._density()}
    def compute(self)->float:
        c=self._components()
        score=self.w["frequency"]*c["frequency_component"]+self.w["entities"]*c["entities_component"]+self.w["actions"]*c["actions_component"]+self.w["relations"]*c["relations_component"]+self.w["density"]*c["density_component"]
        if self.unique_actions<self.cal.min_actions_for_systemic or self.unique_entities<self.cal.min_entities_for_systemic:
            score*=1.0-self.cal.penalty_if_too_simple
        return round(self._clamp(score),3)
    def explain(self)->Dict[str,Any]:
        c={k:round(v,3) for k,v in self._components().items()}
        c.update({"weights":dict(self.w),"raw":{"frequency":self.frequency,"unique_entities":self.unique_entities,"unique_actions":self.unique_actions,"relations_count":self.relations_count,"subgraph_density":round(self.subgraph_density,6)},"penalty_applied":self.unique_actions<self.cal.min_actions_for_systemic or self.unique_entities<self.cal.min_entities_for_systemic,"complexity_score":self.compute()})
        return c
