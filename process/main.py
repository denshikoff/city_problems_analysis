import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from clean_proceccing import TextPreprocessor
from relations_entity import UrbanProblemsGraphExtractor
from ner_proceccing import UrbanKnowledgeGraph
from ai_agent import run_agent


# ---------- IO HELPERS ----------

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class ArtifactSaver:
    """Сохраняет промежуточные артефакты пайплайна в удобных форматах."""

    def __init__(self, output_dir: str | Path = "artifacts"):
        self.output_dir = ensure_dir(Path(output_dir))
        self.tables_dir = ensure_dir(self.output_dir / "tables")
        self.json_dir = ensure_dir(self.output_dir / "json")
        self.graphs_dir = ensure_dir(self.output_dir / "graphs")
        self.debug_dir = ensure_dir(self.output_dir / "debug")

    def save_dataframe(self, df: pd.DataFrame, name: str) -> Dict[str, str]:
        paths: Dict[str, str] = {}
        csv_path = self.tables_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        paths["csv"] = str(csv_path)

        try:
            xlsx_path = self.tables_dir / f"{name}.xlsx"
            df.to_excel(xlsx_path, index=False)
            paths["xlsx"] = str(xlsx_path)
        except Exception as exc:
            paths["xlsx_error"] = str(exc)

        return paths

    def save_json(self, data: Any, name: str) -> str:
        path = self.json_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return str(path)

    def save_text(self, text: str, name: str) -> str:
        path = self.debug_dir / f"{name}.txt"
        path.write_text(text, encoding="utf-8")
        return str(path)


# ---------- AGENT PAYLOAD ----------
def build_agent_payload(problems_df: pd.DataFrame) -> dict:
    """Формирует payload для аналитического агента только из таблицы проблем."""
    if problems_df is None or problems_df.empty:
        return {"error": "no problems detected"}

    required_cols = [
        "Проблема",
        "Тип_проблемы",
        "Частота_упоминаний",
        "Количество_субъектов",
        "Количество_действий",
        "Плотность_подграфа",
        "Complexity_score",
    ]

    safe_df = problems_df.copy()
    for col in required_cols:
        if col not in safe_df.columns:
            safe_df[col] = None

    problems_for_agent = (
        safe_df.sort_values("Complexity_score", ascending=False)
        .head(20)[required_cols]
        .rename(
            columns={
                "Проблема": "problem",
                "Тип_проблемы": "type",
                "Частота_упоминаний": "frequency",
                "Количество_субъектов": "subjects_count",
                "Количество_действий": "actions_count",
                "Плотность_подграфа": "subgraph_density",
                "Complexity_score": "complexity_score",
            }
        )
        .to_dict("records")
    )

    return {
        "meta": {
            "total_problems": int(len(safe_df)),
            "top_problems_sent": int(len(problems_for_agent)),
        },
        "problems": problems_for_agent,
        "statistics": {
            "complexity_distribution": {
                "min": float(safe_df["Complexity_score"].min()),
                "max": float(safe_df["Complexity_score"].max()),
                "mean": float(safe_df["Complexity_score"].mean()),
            }
        },
    }


# ---------- CORE PIPELINE ----------
def process_items(
    df: pd.DataFrame,
    output_dir: str = "artifacts",
    run_llm_agent: bool = True,
    graph_top_problems: int = 15,
) -> dict:
    print(f"Считано {len(df)} записей")
    saver = ArtifactSaver(output_dir)
    artifact_index: Dict[str, Any] = {"output_dir": str(saver.output_dir), "steps": {}}

    # 0. Исходный датасет
    artifact_index["steps"]["raw_dataset"] = saver.save_dataframe(df, "00_raw_dataset")

    # 1. Очистка / фичи
    preprocessor = TextPreprocessor(language="russian", use_lemmatization=True)
    df_processed = preprocessor.preprocess_dataframe(
        df,
        text_column="Текст",
        date_column="Дата создания",
        address_column="Улица",
        category_column=None,
    )
    df_processed["text_lem"] = df_processed["text_lemmatized_tokens"]

    artifact_index["steps"]["cleaned_dataset"] = saver.save_dataframe(df_processed, "01_cleaned_dataset")
    artifact_index["steps"]["preprocessing_report"] = saver.save_json(
        preprocessor.get_preprocessing_report(df_processed),
        "01_preprocessing_report",
    )

    # 2. NER / сущности
    graph_extractor = UrbanProblemsGraphExtractor()
    entities_df = graph_extractor.extract_entities(df_processed, text_column="Текст")
    entity_stats_df = graph_extractor.get_entity_statistics(entities_df)
    artifact_index["steps"]["entities"] = saver.save_dataframe(entities_df, "02_entities_ner")
    artifact_index["steps"]["entity_statistics"] = saver.save_dataframe(entity_stats_df, "02_entity_statistics")

    # 3. Relations
    relations_df = graph_extractor.extract_with_context(df_processed, text_column="text_lem")
    artifact_index["steps"]["relations"] = saver.save_dataframe(relations_df, "03_relations_with_context")

    # 4. Knowledge graph + metrics
    knowledge_graph = UrbanKnowledgeGraph(relations_df)
    knowledge_graph.build_graph()

    density_metrics = knowledge_graph.calculate_density()
    centrality_metrics = knowledge_graph.calculate_centrality(top_n=20)
    problems_df = knowledge_graph.identify_problems(min_frequency=2)
    summary = knowledge_graph.get_summary_report()
    community_info = knowledge_graph.analyze_communities()

    artifact_index["steps"]["graph_summary"] = saver.save_json(summary, "04_graph_summary")
    artifact_index["steps"]["graph_density"] = saver.save_json(density_metrics, "04_graph_density")

    if getattr(knowledge_graph, "centrality_df", None) is not None and not knowledge_graph.centrality_df.empty:
        artifact_index["steps"]["centrality_full"] = saver.save_dataframe(
            knowledge_graph.centrality_df, "04_centrality_full"
        )

    centrality_top_index: Dict[str, Dict[str, str]] = {}
    for metric_name, metric_df in centrality_metrics.items():
        centrality_top_index[metric_name] = saver.save_dataframe(metric_df, f"04_{metric_name}")
    artifact_index["steps"]["centrality_top"] = centrality_top_index

    artifact_index["steps"]["problems"] = saver.save_dataframe(problems_df, "05_problems")

    if community_info:
        if isinstance(community_info.get("stats"), pd.DataFrame):
            artifact_index["steps"]["communities_stats"] = saver.save_dataframe(
                community_info["stats"], "05_communities_stats"
            )
        artifact_index["steps"]["communities_json"] = saver.save_json(
            {
                "method": community_info.get("method"),
                "communities": community_info.get("communities", {}),
            },
            "05_communities",
        )

    graph_exports = knowledge_graph.export_graph_artifacts(
        output_dir=saver.graphs_dir,
        top_problems=graph_top_problems,
        centrality_df=knowledge_graph.centrality_df,
    )
    artifact_index["steps"]["graph_exports"] = graph_exports

    # 5. Agent
    agent_payload = build_agent_payload(problems_df)
    artifact_index["steps"]["agent_payload"] = saver.save_json(agent_payload, "06_agent_payload")

    agent_result: Dict[str, Any]
    if run_llm_agent and "error" not in agent_payload:
        agent_result = run_agent(agent_payload)
    else:
        agent_result = {"skipped": True, "reason": "disabled or no problems detected"}

    artifact_index["steps"]["agent_result"] = saver.save_json(agent_result, "06_final_agent_report")
    artifact_index_path = saver.save_json(artifact_index, "artifact_index")

    return {
        "df_processed": df_processed,
        "entities_df": entities_df,
        "entity_stats_df": entity_stats_df,
        "relations_df": relations_df,
        "problems_df": problems_df,
        "summary": summary,
        "agent_payload": agent_payload,
        "agent_result": agent_result,
        "artifact_index": artifact_index,
        "artifact_index_path": artifact_index_path,
    }


# ---------- CLI ENTRYPOINT ----------
def main():
    parser = argparse.ArgumentParser(
        description="Анализ городских обращений и выявление комплексных проблем"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data_all.xlsx",
        help="Путь к Excel файлу с обращениями",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts",
        help="Каталог для сохранения всех промежуточных и итоговых артефактов",
    )
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Не запускать локальную LLM-модель для финального отчёта",
    )
    parser.add_argument(
        "--graph-top-problems",
        type=int,
        default=15,
        help="Сколько топ-проблем включать в PNG визуализацию графа",
    )

    args = parser.parse_args()

    df = pd.read_excel(args.input)
    result = process_items(
        df,
        output_dir=args.output_dir,
        run_llm_agent=not args.skip_agent,
        graph_top_problems=args.graph_top_problems,
    )

    print("✅ Анализ завершён. Результаты сохранены.")
    print(f"📁 Каталог артефактов: {args.output_dir}")
    print(f"🧾 Индекс артефактов: {result['artifact_index_path']}")


if __name__ == "__main__":
    main()
