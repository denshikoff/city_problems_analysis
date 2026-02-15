import re
import pandas as pd


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def retrieve_relevant_problems(df: pd.DataFrame, query: str, top_k: int = 10) -> pd.DataFrame:
    q = normalize_text(query)
    if not q:
        return df.sort_values("Complexity_score", ascending=False).head(top_k)

    prob = df.copy()
    prob["_match"] = (
        prob["Проблема"].str.lower().str.contains(q, regex=False).astype(int) * 3
        + prob["Тип_проблемы"].str.lower().str.contains(q, regex=False).astype(int) * 2
    )

    if prob["_match"].sum() == 0:
        tokens = [t for t in re.split(r"[^\wа-яё]+", q, flags=re.IGNORECASE) if len(t) >= 3]
        if tokens:
            def token_score(row) -> int:
                text = f"{row['Проблема']} {row['Тип_проблемы']}".lower()
                return sum(1 for t in tokens if t in text)
            prob["_match"] = prob.apply(token_score, axis=1)

    prob["_score"] = prob["_match"] + (prob["Complexity_score"] * 1.5)
    return (
        prob.sort_values(["_score", "Complexity_score"], ascending=False)
        .head(top_k)
        .drop(columns=["_match", "_score"])
    )
