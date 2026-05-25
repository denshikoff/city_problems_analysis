from __future__ import annotations
import json, re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import networkx as nx
import pandas as pd
from complex_problem_score import ComplexProblemScorer

def norm(x:Any)->str: return re.sub(r"\s+"," ",str(x or "").lower().replace("ё","е")).strip(" .,:;!?-—")
def top(xs:Iterable[Any], n:int=12)->List[str]:
    c=Counter(norm(x) for x in xs if norm(x)); return [k for k,_ in c.most_common(n)]
def fnum(x, default=0.0):
    try: return default if pd.isna(x) else float(x)
    except Exception: return default

@dataclass
class ProblemCandidate:
    candidate_id:str; title:str; problem_type:str; complexity_score:float; score_factors:Dict[str,Any]
    appeal_ids:List[str]; evidence_appeals:List[Dict[str,Any]]; entities:List[str]; actions:List[str]; actors:List[str]
    problem_anchors:List[str]; territories:List[str]; thematic_areas:List[str]; time_window:Dict[str,Optional[str]]
    relations:List[Dict[str,Any]]; metrics:Dict[str,Any]; llm_summary:Optional[Dict[str,Any]]=None
    def to_dict(self): return asdict(self)
    def to_flat_row(self):
        return {"candidate_id":self.candidate_id,"Проблема":self.title,"Тип_проблемы":self.problem_type,"Complexity_score":self.complexity_score,"Частота_упоминаний":self.metrics.get("frequency",0),"Количество_субъектов":len(self.actors),"Количество_действий":len(self.actions),"Количество_связей":self.metrics.get("relations_count",0),"Плотность_подграфа":self.metrics.get("subgraph_density",0),"Территории":"; ".join(self.territories[:8]),"Проблемные_признаки":"; ".join(self.problem_anchors[:8]),"Ключевые_сущности":"; ".join(self.entities[:12]),"Действия":"; ".join(self.actions[:12]),"Подтверждающие_обращения":len(self.appeal_ids)}

class ProblemCandidateBuilder:
    def __init__(self, relations_df:pd.DataFrame, processed_df:pd.DataFrame|None=None):
        self.relations_df=relations_df.copy() if relations_df is not None else pd.DataFrame(); self.processed_df=processed_df.copy() if processed_df is not None else pd.DataFrame(); self.graph=nx.MultiDiGraph()
    def build_graph(self):
        self.graph.clear()
        for _,r in self.relations_df.iterrows():
            aid=str(r.get("appeal_id") or f"appeal_{r.get('doc_index',0)}"); subj=norm(r.get("Субъект")) or "жители"; act=norm(r.get("Связь")) or "сообщает"; obj=norm(r.get("Объект")) or "объект"; anch=norm(r.get("Проблемный_признак")) or "проблемный сигнал"; theme=norm(r.get("Тема")) or "другое"; addr=norm(r.get("Адрес"))
            for n,t in [(aid,"appeal"),(subj,"actor"),(obj,"object"),(anch,"problem_anchor"),(theme,"theme")]: self.graph.add_node(n,type=t,label=n)
            self.graph.add_edge(aid,obj,relation="mentions",appeal_id=aid); self.graph.add_edge(aid,anch,relation="has_problem_anchor",appeal_id=aid); self.graph.add_edge(subj,obj,relation=act,appeal_id=aid); self.graph.add_edge(obj,anch,relation="has_sign",appeal_id=aid); self.graph.add_edge(obj,theme,relation="belongs_to_theme",appeal_id=aid)
            if addr: self.graph.add_node(addr,type="territory",label=addr); self.graph.add_edge(aid,addr,relation="located_at",appeal_id=aid); self.graph.add_edge(obj,addr,relation="observed_at",appeal_id=aid)
        return self.graph
    def _key(self,r): return (norm(r.get("Объект")) or norm(r.get("Тема")) or "городская проблема", norm(r.get("Проблемный_признак")) or "проблемный сигнал")
    def _density(self,g):
        nodes=set()
        for _,r in g.iterrows():
            for col in ["appeal_id","Субъект","Объект","Проблемный_признак","Тема","Адрес"]:
                val=str(r.get(col) or "") if col=="appeal_id" else norm(r.get(col));
                if val: nodes.add(val)
        sg=self.graph.subgraph(nodes).copy(); return round(min(float(nx.density(sg)),1.0),6) if sg.number_of_nodes()>1 else 0.0
    @staticmethod
    def _ptype(g): return (top(g.get("Тема",[]),1) or top(g.get("Категория_источника",[]),1) or ["другое"])[0]
    @staticmethod
    def _title(key,g):
        obj,anch=key; a=(top(g.get("Проблемный_признак",[]),1) or [anch])[0]
        return f"{obj}: {a}" if a and a!="проблемный сигнал" else obj
    def _evidence(self,g,limit=5):
        g=g.copy(); g["_rank"]=g.get("emotion_score",0).map(fnum)+g.get("urgency_flag",False).astype(float)*.5
        out=[]
        for _,r in g.sort_values("_rank",ascending=False).drop_duplicates("appeal_id").head(limit).iterrows():
            out.append({"appeal_id":str(r.get("appeal_id") or ""),"doc_index":int(r.get("doc_index") or 0),"date":r.get("Дата"),"address":norm(r.get("Адрес")),"category":r.get("Категория_источника"),"text":str(r.get("raw_text") or r.get("Контекст") or "")[:900],"emotion_score":fnum(r.get("emotion_score")),"urgency_flag":bool(r.get("urgency_flag") or False)})
        return out
    def _relations(self,g,limit=20):
        out=[]; seen=set()
        for _,r in g.iterrows():
            item={"subject":norm(r.get("Субъект")),"action":norm(r.get("Связь")),"object":norm(r.get("Объект")),"problem_anchor":norm(r.get("Проблемный_признак")),"appeal_id":str(r.get("appeal_id") or "")}; key=tuple(item.values())
            if key not in seen: seen.add(key); out.append(item)
            if len(out)>=limit: break
        return out
    def build_candidates(self,min_appeals=3,min_relations=5,max_candidates:Optional[int]=200):
        if self.graph.number_of_nodes()==0: self.build_graph()
        if self.relations_df.empty: return []
        tmp=self.relations_df.copy(); tmp["_key"]=tmp.apply(self._key,axis=1); cands=[]
        for key,g in tmp.groupby("_key"):
            aids=[str(x) for x in g["appeal_id"].dropna().unique().tolist()]; freq=len(aids); rels=len(g)
            if freq<min_appeals or rels<min_relations: continue
            actors=top(g.get("Субъект",[])); actions=top(g.get("Связь",[])); objects=top(g.get("Объект",[])); anchors=top(g.get("Проблемный_признак",[])); terr=top([x for x in g.get("Адрес",[]) if norm(x)]); themes=top(g.get("Тема",[]),8)
            entities=top(objects+actors+anchors+terr+themes,20); density=self._density(g)
            scorer=ComplexProblemScorer(freq,len(entities),len(actions),density,rels); dates=[str(x) for x in g.get("Дата",pd.Series(dtype=str)).dropna().unique().tolist() if str(x)!="None"]
            metrics={"frequency":freq,"relations_count":int(rels),"unique_entities":len(entities),"unique_actions":len(actions),"subgraph_density":density,"avg_emotion_score":round(float(g.get("emotion_score",pd.Series([0])).map(fnum).mean() or 0),3),"urgent_appeals":int(g.get("urgency_flag",pd.Series(dtype=bool)).fillna(False).astype(bool).sum())}
            cands.append(ProblemCandidate(f"kp_{len(cands)+1:04d}",self._title(key,g),self._ptype(g),scorer.compute(),scorer.explain(),aids[:500],self._evidence(g),entities,actions,actors,anchors,terr,themes,{"start":min(dates) if dates else None,"end":max(dates) if dates else None},self._relations(g),metrics))
        cands.sort(key=lambda c:c.complexity_score,reverse=True); cands=cands[:max_candidates] if max_candidates else cands
        for i,c in enumerate(cands,1): c.candidate_id=f"kp_{i:04d}"
        return cands
    @staticmethod
    def to_dataframe(candidates): return pd.DataFrame([c.to_flat_row() for c in candidates])
    @staticmethod
    def save_jsonl(candidates,path):
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("w",encoding="utf-8") as f:
            for c in candidates: f.write(json.dumps(c.to_dict(),ensure_ascii=False,default=str)+"\n")
        return str(p)
