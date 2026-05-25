from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from clean_proceccing import TextPreprocessor
from relations_entity import UrbanProblemsGraphExtractor
from ner_proceccing import UrbanKnowledgeGraph
from candidate_builder import ProblemCandidateBuilder
from llm_service import LLMService
from ai_agent import run_agent

class ArtifactSaver:
    def __init__(self, output_dir):
        self.output_dir=Path(output_dir); self.tables_dir=self.output_dir/"tables"; self.json_dir=self.output_dir/"json"; self.graphs_dir=self.output_dir/"graphs"
        for p in [self.output_dir,self.tables_dir,self.json_dir,self.graphs_dir]: p.mkdir(parents=True,exist_ok=True)
    def save_dataframe(self,df,name):
        paths={}; csv=self.tables_dir/f"{name}.csv"; df.to_csv(csv,index=False,encoding="utf-8-sig"); paths["csv"]=str(csv)
        try: xlsx=self.tables_dir/f"{name}.xlsx"; df.to_excel(xlsx,index=False); paths["xlsx"]=str(xlsx)
        except Exception as e: paths["xlsx_error"]=str(e)
        return paths
    def save_json(self,data,name):
        p=self.json_dir/f"{name}.json"; p.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding="utf-8"); return str(p)
    def save_jsonl_candidates(self,cands,name="problem_candidates"): return ProblemCandidateBuilder.save_jsonl(cands,self.json_dir/f"{name}.jsonl")

def read_dataset(path,nrows=None):
    p=Path(path)
    if p.suffix.lower() in [".xlsx",".xls"]: return pd.read_excel(p,nrows=nrows)
    if p.suffix.lower()==".csv": return pd.read_csv(p,nrows=nrows)
    raise ValueError("Поддерживаются .xlsx/.xls/.csv")

def add_summaries(candidates, run_llm=False):
    service=LLMService(backend="ollama" if run_llm else "heuristic")
    for c in candidates: c.llm_summary=service.summarize_candidate(c.to_dict())
    return candidates

def build_agent_payload(candidates):
    rows=[c.to_dict() for c in candidates]; scores=[float(x.get("complexity_score") or 0) for x in rows]
    return {"meta":{"total_candidates":len(rows),"top_sent":min(20,len(rows))},"candidates":rows[:20],"statistics":{"complexity_distribution":{"min":min(scores) if scores else 0,"max":max(scores) if scores else 0,"mean":sum(scores)/len(scores) if scores else 0}}}

def process_items(df:pd.DataFrame, output_dir="artifacts/default", *, text_column:Optional[str]=None, date_column:Optional[str]=None, address_column:Optional[str]=None, category_column:Optional[str]=None, max_rows:Optional[int]=None, min_appeals:int=3, min_relations:int=5, max_candidates:int=200, run_llm:bool=False)->Dict[str,Any]:
    saver=ArtifactSaver(output_dir); idx={"output_dir":str(saver.output_dir),"steps":{}}
    idx["steps"]["raw_dataset"]=saver.save_dataframe(df.head(max_rows) if max_rows else df,"00_raw_dataset")
    pre=TextPreprocessor(use_lemmatization=True); dfd=pre.preprocess_dataframe(df,text_column,date_column,address_column,category_column,max_rows=max_rows)
    idx["column_mapping"]={"text":dfd["source_text_column"].iloc[0] if len(dfd) else text_column,"date":dfd["source_date_column"].iloc[0] if len(dfd) else date_column,"address":dfd["source_address_column"].iloc[0] if len(dfd) else address_column,"category":dfd["source_category_column"].iloc[0] if len(dfd) else category_column}
    idx["steps"]["cleaned_dataset"]=saver.save_dataframe(dfd,"01_cleaned_dataset"); idx["steps"]["preprocessing_report"]=saver.save_json(pre.get_preprocessing_report(dfd),"01_preprocessing_report")
    ext=UrbanProblemsGraphExtractor(); ent=ext.extract_entities(dfd); rel=ext.extract_with_context(dfd); stat=ext.get_entity_statistics(ent)
    idx["steps"]["entities"]=saver.save_dataframe(ent,"02_entities"); idx["steps"]["entity_statistics"]=saver.save_dataframe(stat,"02_entity_statistics"); idx["steps"]["relations"]=saver.save_dataframe(rel,"03_relations")
    kg=UrbanKnowledgeGraph(rel,processed_df=dfd); kg.build_graph(); density=kg.calculate_density(); kg.calculate_centrality(top_n=30); kg.identify_problems(min_frequency=min_appeals,min_relations=min_relations,max_candidates=max_candidates)
    candidates=add_summaries(kg.candidates,run_llm=run_llm); cand_df=ProblemCandidateBuilder.to_dataframe(candidates)
    idx["steps"]["graph_density"]=saver.save_json(density,"04_graph_density"); idx["steps"]["graph_summary"]=saver.save_json(kg.get_summary_report(),"04_graph_summary")
    if not kg.centrality_df.empty: idx["steps"]["centrality_full"]=saver.save_dataframe(kg.centrality_df,"04_centrality_full")
    idx["steps"]["problem_candidates_csv"]=saver.save_dataframe(cand_df,"05_problem_candidates"); idx["steps"]["problem_candidates_jsonl"]=saver.save_jsonl_candidates(candidates); idx["steps"]["graph_exports"]=kg.export_graph_artifacts(saver.graphs_dir)
    payload=build_agent_payload(candidates); idx["steps"]["agent_payload"]=saver.save_json(payload,"06_agent_payload"); idx["steps"]["agent_result"]=saver.save_json(run_agent(payload),"06_final_agent_report")
    artifact_index_path=saver.save_json(idx,"artifact_index")
    return {"df_processed":dfd,"entities_df":ent,"relations_df":rel,"candidates":candidates,"problems_df":cand_df,"artifact_index":idx,"artifact_index_path":artifact_index_path}

def main():
    p=argparse.ArgumentParser(description="Анализ городских обращений и кандидаты комплексных проблем")
    p.add_argument("--input",default="data_all.xlsx"); p.add_argument("--output-dir",default="city_assistant_ui/artifacts/default"); p.add_argument("--text-column"); p.add_argument("--date-column"); p.add_argument("--address-column"); p.add_argument("--category-column"); p.add_argument("--max-rows",type=int); p.add_argument("--min-appeals",type=int,default=3); p.add_argument("--min-relations",type=int,default=5); p.add_argument("--max-candidates",type=int,default=200); p.add_argument("--run-llm",action="store_true")
    a=p.parse_args(); df=read_dataset(a.input,nrows=a.max_rows)
    res=process_items(df,output_dir=a.output_dir,text_column=a.text_column,date_column=a.date_column,address_column=a.address_column,category_column=a.category_column,min_appeals=a.min_appeals,min_relations=a.min_relations,max_candidates=a.max_candidates,run_llm=a.run_llm)
    print("✅ Анализ завершен"); print(f"Артефакты: {a.output_dir}"); print(f"Кандидатов КП: {len(res['candidates'])}"); print(f"Индекс: {res['artifact_index_path']}")
if __name__=="__main__": main()
