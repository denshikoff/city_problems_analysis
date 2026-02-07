import pandas as pd
import json
from clean_proceccing import TextPreprocessor
from relations_entity import UrbanProblemsGraphExtractor
from ner_proceccing import UrbanKnowledgeGraph

def build_agent_payload(
    summary: dict,
    density_metrics: dict,
    centrality_metrics: dict,
    problems_df: pd.DataFrame,
    relations_df: pd.DataFrame
) -> dict:

    top_entities = [
        {
            "entity": row["entity"],
            "degree": row["degree"],
            "betweenness": row.get("betweenness", None)
        }
        for _, row in centrality_metrics["degree"].head(10).iterrows()
    ]

    key_relations = (
        relations_df
        .groupby(["subject", "action", "object"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(10)
        .to_dict("records")
    )

    problems = problems_df.head(10).to_dict("records")

    return {
        "meta": {
            "records_count": int(summary.get("total_records", 0))
        },
        "graph_summary": {
            "top_entities": top_entities,
            "key_relations": key_relations,
            "density": density_metrics
        },
        "problems": problems,
        "signals": {
            "entity_concentration": "high" if len(top_entities) < 5 else "medium",
            "relation_repetition": "high" if len(key_relations) > 5 else "low"
        }
    }


def process_items(items):
    df = pd.DataFrame(items)
    print(f"Считано {len(df)} записей")

    # 2️⃣ Предобработка текста
    preprocessor = TextPreprocessor(language="russian", use_lemmatization=True)
    df_processed = preprocessor.preprocess_dataframe(
        df,
        text_column="Текст",
        date_column="Дата создания",
        address_column="Улица",
        category_column=None,
    )

    report = preprocessor.get_preprocessing_report(df_processed)

    # 3️⃣ Извлечение связей субъект-действие-объект
    # Используем колонку с лемматизированными токенами
    df_processed['text_lem'] = df_processed['text_lemmatized_tokens']
    
    graph_extractor = UrbanProblemsGraphExtractor()
    relations_df = graph_extractor.extract_with_context(df_processed, text_column='text_lem')
    
    print(f"Извлечено {len(relations_df)} уникальных связей субъект-действие-объект")

       # 4️⃣ Построение графа знаний и анализ NER
    knowledge_graph = UrbanKnowledgeGraph(relations_df)
    nx_graph = knowledge_graph.build_graph()                # строим граф
    density_metrics = knowledge_graph.calculate_density()   # рассчитываем плотность
    centrality_metrics = knowledge_graph.calculate_centrality(top_n=20)  # центральность
    problems_df = knowledge_graph.identify_problems(min_frequency=2)      # выявляем проблемы
    
        # 6️⃣ Генерация сводного отчета
    summary = knowledge_graph.get_summary_report()

    # 7️⃣ Сохраняем данные для ИИ-агента
    output_json = "processed_for_ai.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            "preprocessed_dataframe": json.loads(df_processed.to_json(orient='records', date_format='iso')),
            "relations": relations_df.to_dict(orient='records'),
            "graph_metrics": density_metrics,
            "centrality_metrics": {k: v.to_dict('records') for k, v in centrality_metrics.items()},
            "problems": problems_df.to_dict(orient='records'),
            "summary": summary
        }, f, ensure_ascii=False, indent=2)

    agent_payload = build_agent_payload(
        summary,
        density_metrics,
        centrality_metrics,
        problems_df,
        relations_df
    )

    with open("agent_payload.json", "w", encoding="utf-8") as f:
        json.dump(agent_payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()