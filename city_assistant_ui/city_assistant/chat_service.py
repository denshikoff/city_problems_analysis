import json
import numpy as np
import pandas as pd
from .retrieval import retrieve_relevant_problems, normalize_text


class ChatService:
    def __init__(self, problems_df: pd.DataFrame, chat_mode: str = "heuristic"):
        self.df = problems_df
        self.chat_mode = chat_mode

    def answer(self, user_query: str, top_k_ctx: int = 10) -> str:
        ctx = retrieve_relevant_problems(self.df, user_query, top_k=top_k_ctx)

        if self.chat_mode == "llm":
            # Заглушка: позже подключим run_agent / API
            payload = self._build_llm_payload(ctx)
            return "```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```"

        return self._heuristic_answer(user_query, ctx)

    def _heuristic_answer(self, user_query: str, ctx: pd.DataFrame) -> str:
        q = normalize_text(user_query)

        if any(k in q for k in ["топ", "самые", "главные", "ключевые"]):
            lines = ["Вот топ проблем по комплексности:"]
            for i, row in enumerate(ctx.sort_values("Complexity_score", ascending=False).head(10).itertuples(), 1):
                lines.append(
                    f"{i}. **{row.Проблема}** ({row.Тип_проблемы}) — score={row.Complexity_score:.3f}, "
                    f"частота={row.Частота_упоминаний}, субъекты={row.Количество_субъектов}, "
                    f"действия={row.Количество_действий}, плотность={row.Плотность_подграфа:.3f}"
                )
            return "\n".join(lines)

        if any(k in q for k in ["почему", "объясни", "поясни"]):
            one = retrieve_relevant_problems(self.df, user_query, top_k=1)
            if one.empty:
                return "Не нашёл проблему по запросу. Попробуй уточнить формулировку."
            r = one.iloc[0]
            return (
                f"**Почему {r['Проблема']} выглядит комплексной:**\n"
                f"- complexity_score: **{r['Complexity_score']:.3f}**\n"
                f"- частота: **{int(r['Частота_упоминаний'])}**\n"
                f"- субъекты: **{int(r['Количество_субъектов'])}**\n"
                f"- действия: **{int(r['Количество_действий'])}**\n"
                f"- плотность: **{float(r['Плотность_подграфа']):.3f}**"
            )

        total = len(self.df)
        systemic = int((self.df["Complexity_score"] >= 0.7).sum())
        lines = [
            f"В базе проблем: **{total}**, системных (score ≥ 0.7): **{systemic}**.",
            "По твоему запросу наиболее релевантны:"
        ]
        for i, row in enumerate(ctx.head(5).itertuples(), 1):
            lines.append(f"{i}. **{row.Проблема}** ({row.Тип_проблемы}) — score={row.Complexity_score:.3f}")
        lines.append("\nХочешь: **топ-10**, **почему проблема комплексная**, или фильтр по типу?")
        return "\n".join(lines)

    def _build_llm_payload(self, ctx: pd.DataFrame) -> dict:
        return {
            "meta": {"top_problems_sent": int(len(ctx))},
            "problems": [
                {
                    "problem": r["Проблема"],
                    "type": r["Тип_проблемы"],
                    "frequency": int(r["Частота_упоминаний"]),
                    "subjects_count": int(r["Количество_субъектов"]),
                    "actions_count": int(r["Количество_действий"]),
                    "subgraph_density": float(r["Плотность_подграфа"]),
                    "complexity_score": float(r["Complexity_score"]),
                }
                for _, r in ctx.sort_values("Complexity_score", ascending=False).iterrows()
            ],
            "statistics": {
                "complexity_distribution": {
                    "min": float(ctx["Complexity_score"].min()) if len(ctx) else 0.0,
                    "max": float(ctx["Complexity_score"].max()) if len(ctx) else 0.0,
                    "mean": float(ctx["Complexity_score"].mean()) if len(ctx) else 0.0,
                    "p90": float(np.percentile(ctx["Complexity_score"], 90)) if len(ctx) else 0.0,
                }
            }
        }
