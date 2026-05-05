from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from candidate_builder import ProblemCandidateBuilder

class UrbanKnowledgeGraph:
    """Совместимый фасад: старый API + новые кандидаты problem_candidates.jsonl."""
    def __init__(self, relations_df:pd.DataFrame, processed_df:Optional[pd.DataFrame]=None, log_level:str="INFO"):
        self.relations_df=relations_df.copy() if relations_df is not None else pd.DataFrame(); self.processed_df=processed_df.copy() if processed_df is not None else pd.DataFrame(); self.builder=ProblemCandidateBuilder(self.relations_df,self.processed_df); self.graph=nx.MultiDiGraph(); self.centrality_df=pd.DataFrame(); self.problems=[]; self.candidates=[]
    def build_graph(self): self.graph=self.builder.build_graph(); return self.graph
    def calculate_density(self)->Dict[str,float]:
        if self.graph.number_of_nodes()==0: self.build_graph()
        if self.graph.number_of_nodes()<2: return {"density":0.0,"directed_density":0.0,"edges_per_node":0.0}
        return {"density":round(min(float(nx.density(self.graph.to_undirected())),1.0),6),"directed_density":round(min(float(nx.density(self.graph)),1.0),6),"edges_per_node":round(self.graph.number_of_edges()/max(self.graph.number_of_nodes(),1),6)}
    def calculate_centrality(self, top_n:int=20):
        if self.graph.number_of_nodes()==0: self.build_graph()
        if self.graph.number_of_nodes()==0: return {}
        degree=nx.degree_centrality(self.graph); indeg=nx.in_degree_centrality(self.graph); outdeg=nx.out_degree_centrality(self.graph); bet={n:0.0 for n in self.graph.nodes}
        if self.graph.number_of_nodes()<=5000: bet=nx.betweenness_centrality(self.graph,normalized=True)
        self.centrality_df=pd.DataFrame([{"Узел":n,"Тип":self.graph.nodes[n].get("type","unknown"),"Degree":degree.get(n,0),"In_Degree":indeg.get(n,0),"Out_Degree":outdeg.get(n,0),"Betweenness":bet.get(n,0),"Степень":int(self.graph.degree(n))} for n in self.graph.nodes]).sort_values("Degree",ascending=False)
        return {"degree_top":self.centrality_df.nlargest(top_n,"Degree"),"betweenness_top":self.centrality_df.nlargest(top_n,"Betweenness")}
    def identify_problems(self, min_frequency:int=3, min_relations:int=5, max_candidates:int|None=200):
        self.candidates=self.builder.build_candidates(min_appeals=min_frequency,min_relations=min_relations,max_candidates=max_candidates); df=ProblemCandidateBuilder.to_dataframe(self.candidates); self.problems=df.to_dict("records") if not df.empty else []; return df
    def analyze_communities(self):
        if self.graph.number_of_nodes()==0: self.build_graph()
        if self.graph.number_of_nodes()==0: return {}
        comps=list(nx.connected_components(self.graph.to_undirected())); stats=[{"Сообщество":i,"Размер":len(nodes),"Узлы":list(nodes)[:20]} for i,nodes in enumerate(comps) if len(nodes)>1]
        return {"method":"connected_components","communities_count":len(comps),"stats":pd.DataFrame(stats)}
    def get_summary_report(self): return {"nodes":int(self.graph.number_of_nodes()),"edges":int(self.graph.number_of_edges()),"relations_rows":int(len(self.relations_df)),"candidates":int(len(self.candidates)),"density":self.calculate_density()}
    def export_graph_artifacts(self, output_dir, top_problems:int=15, centrality_df:Optional[pd.DataFrame]=None):
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); paths={}
        if self.graph.number_of_nodes()==0: self.build_graph()
        g=nx.DiGraph()
        for u,v,d in self.graph.edges(data=True):
            g.add_node(u,**{k:str(vv) for k,vv in self.graph.nodes[u].items()}); g.add_node(v,**{k:str(vv) for k,vv in self.graph.nodes[v].items()}); g.add_edge(u,v,**{k:str(vv) for k,vv in d.items()})
        try: nx.write_graphml(g,out/"knowledge_graph.graphml"); paths["graphml"]=str(out/"knowledge_graph.graphml")
        except Exception as e: paths["graphml_error"]=str(e)
        if self.candidates:
            nodes=set()
            for c in self.candidates[:top_problems]: nodes.update(c.entities[:6]); nodes.update(c.problem_anchors[:3])
            sg=g.subgraph([n for n in nodes if n in g]).copy()
            if sg.number_of_nodes()>1:
                plt.figure(figsize=(14,9)); pos=nx.spring_layout(sg,seed=42,k=.6); nx.draw_networkx_nodes(sg,pos,node_size=500,alpha=.85); nx.draw_networkx_edges(sg,pos,alpha=.25,arrows=True); nx.draw_networkx_labels(sg,pos,font_size=8); plt.axis("off"); plt.tight_layout(); plt.savefig(out/"top_problem_graph.png",dpi=180); plt.close(); paths["top_problem_graph_png"]=str(out/"top_problem_graph.png")
        return paths
