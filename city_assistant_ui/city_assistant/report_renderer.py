def render_markdown_report(candidates, top_n=10):
    lines=["# Отчет по комплексным городским проблемам",""]
    for i,c in enumerate(candidates[:top_n],1):
        m=c.get("metrics",{}) or {}; lines += [f"## {i}. {c.get('title')}",f"- ID: `{c.get('candidate_id')}`",f"- Тип: {c.get('problem_type')}",f"- Complexity_score: {float(c.get('complexity_score') or 0):.3f}",f"- Обращений: {m.get('frequency')}; связей: {m.get('relations_count')}",""]
    return "\n".join(lines)
