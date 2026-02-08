import pandas as pd
import json
import argparse

from clean_proceccing import TextPreprocessor
from relations_entity import UrbanProblemsGraphExtractor
from ner_proceccing import UrbanKnowledgeGraph
from ai_agent import run_agent   # ← обязательно импортируй
from complex_problem_score import ComplexProblemScorer

# ---------- AGENT PAYLOAD ----------
def build_agent_payload(problems_df: pd.DataFrame) -> dict:
    """
    Формирует payload для аналитического агента.
    Все Complexity_score рассчитаны ПО ПРОБЛЕМАМ.
    """

    if problems_df is None or problems_df.empty:
        return {"error": "no problems detected"}

    # Берём только осмысленные поля
    required_cols = [
        "Проблема",
        "Тип_проблемы",
        "Частота_упоминаний",
        "Количество_субъектов",
        "Количество_действий",
        "Плотность_подграфа",
        "Complexity_score"
    ]

    problems_for_agent = (
        problems_df
        .sort_values("Complexity_score", ascending=False)
        .head(20)
        [required_cols]
        .rename(columns={
            "Проблема": "problem",
            "Тип_проблемы": "type",
            "Частота_упоминаний": "frequency",
            "Количество_субъектов": "subjects_count",
            "Количество_действий": "actions_count",
            "Плотность_подграфа": "subgraph_density",
            "Complexity_score": "complexity_score"
        })
        .to_dict("records")
    )

    payload = {
        "meta": {
            "total_problems": int(len(problems_df)),
            "top_problems_sent": int(len(problems_for_agent))
        },
        "problems": problems_for_agent,
        "statistics": {
            "complexity_distribution": {
                "min": float(problems_df["Complexity_score"].min()),
                "max": float(problems_df["Complexity_score"].max()),
                "mean": float(problems_df["Complexity_score"].mean())
            }
        }
    }

    return payload


# ---------- CORE PIPELINE ----------

def process_items(df: pd.DataFrame) -> dict:
    print(f"Считано {len(df)} записей")

    preprocessor = TextPreprocessor(language="russian", use_lemmatization=True)
    df_processed = preprocessor.preprocess_dataframe(
        df,
        text_column="Текст",
        date_column="Дата создания",
        address_column="Улица",
        category_column=None,
    )

    df_processed["text_lem"] = df_processed["text_lemmatized_tokens"]

    graph_extractor = UrbanProblemsGraphExtractor()
    relations_df = graph_extractor.extract_with_context(
        df_processed, text_column="text_lem"
    )

    knowledge_graph = UrbanKnowledgeGraph(relations_df)
    knowledge_graph.build_graph()

    density_metrics = knowledge_graph.calculate_density()
    centrality_metrics = knowledge_graph.calculate_centrality(top_n=20)
    problems_df = knowledge_graph.identify_problems(min_frequency=2)
    summary = knowledge_graph.get_summary_report()

    agent_payload = build_agent_payload(
        summary,
        density_metrics,
        centrality_metrics,
        problems_df,
        relations_df
    )

    agent_result = run_agent(agent_payload)

    return {
        "agent_payload": agent_payload,
        "agent_result": agent_result
    }

# ---------- CLI ENTRYPOINT ----------

def main():
    parser = argparse.ArgumentParser(
        description="Анализ городских обращений и выявление комплексных проблем"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data_voronesh.xlsx",
        help="Путь к Excel файлу с обращениями"
    )

    args = parser.parse_args()

    df = pd.read_excel(args.input)

    result = process_items(df)

    with open("agent_payload.json", "w", encoding="utf-8") as f:
        json.dump(result["agent_payload"], f, ensure_ascii=False, indent=2)

    with open("final_agent_report.json", "w", encoding="utf-8") as f:
        json.dump(result["agent_result"], f, ensure_ascii=False, indent=2)

    print("✅ Анализ завершён. Результаты сохранены.")

# ---------- RUN ----------

if __name__ == "__main__":
    main()