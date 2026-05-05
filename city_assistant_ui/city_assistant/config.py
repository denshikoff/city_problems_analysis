from dataclasses import dataclass
import os
@dataclass
class AppConfig:
    scenario_id:str=os.getenv("CITY_ASSISTANT_SCENARIO","default")
    candidates_jsonl:str=os.getenv("CITY_ASSISTANT_CANDIDATES_JSONL","json/problem_candidates.jsonl")
    problems_csv:str=os.getenv("CITY_ASSISTANT_PROBLEMS_CSV","tables/05_problem_candidates.csv")
    chat_mode:str=os.getenv("CITY_ASSISTANT_CHAT_MODE","heuristic")
    top_k_ctx_default:int=int(os.getenv("CITY_ASSISTANT_TOP_K","10"))
