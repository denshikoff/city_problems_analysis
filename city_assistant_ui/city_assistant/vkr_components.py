from __future__ import annotations

import html
import math
from typing import Any, Dict, List

import streamlit as st

BLUE = "#0b63ce"
BLUE_DARK = "#073b7a"
BORDER = "#dce6f5"
TEXT = "#0b1b35"
MUTED = "#66758f"
BG = "#f6f9fe"


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def score_level(score: float) -> tuple[str, str]:
    if score >= 0.70:
        return "высокий", "danger"
    if score >= 0.45:
        return "средний", "warning"
    return "умеренный", "success"


def inject_vkr_css() -> None:
    st.markdown(
        f"""
<style>
:root {{
  --vkr-blue: {BLUE};
  --vkr-blue-dark: {BLUE_DARK};
  --vkr-border: {BORDER};
  --vkr-text: {TEXT};
  --vkr-muted: {MUTED};
  --vkr-bg: {BG};
}}
#MainMenu, footer, header {{visibility: hidden;}}
.block-container {{
  max-width: 100% !important;
  padding-top: 0.7rem !important;
  padding-left: 7.2rem !important;
  padding-right: 2.1rem !important;
}}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #eef6ff 0%, #f8fbff 100%);
  border-right: 1px solid var(--vkr-border);
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: var(--vkr-text); }}
.vkr-shell {{ color: var(--vkr-text); }}
.vkr-topbar {{
  height: 66px;
  border-bottom: 1px solid var(--vkr-border);
  background: rgba(255,255,255,.96);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: -0.7rem -2.1rem 1.2rem -7.2rem;
  padding: 0 2.0rem 0 1.2rem;
  position: sticky;
  top: 0;
  z-index: 30;
  box-shadow: 0 4px 18px rgba(18, 45, 82, .05);
}}
.vkr-brand {{ display:flex; align-items:center; gap:14px; font-weight:800; font-size:19px; color: var(--vkr-text); }}
.vkr-logo {{
  width: 38px; height: 38px; border-radius: 10px;
  display:flex; align-items:center; justify-content:center;
  background: linear-gradient(135deg, #0d6bdc, #084a9e);
  color:white; font-size: 21px; box-shadow: 0 6px 16px rgba(13, 107, 220, .24);
}}
.vkr-nav {{ display:flex; align-items:center; gap: 22px; color:#66758f; font-weight:650; }}
.vkr-nav span.active {{ color: var(--vkr-blue); border-bottom: 3px solid var(--vkr-blue); padding: 22px 8px 18px; }}
.vkr-nav span {{ padding: 22px 4px 18px; white-space: nowrap; }}
.vkr-icons {{ display:flex; align-items:center; gap:16px; color:#73809a; font-size:22px; }}
.vkr-rail {{
  position: fixed; left:0; top:66px; bottom:0; width:70px; z-index:20;
  background:white; border-right:1px solid var(--vkr-border);
  display:flex; flex-direction:column; align-items:center; padding-top:24px; gap:20px;
}}
.vkr-rail .item {{ width:44px; height:44px; display:flex; align-items:center; justify-content:center; border-radius:12px; color:#5f6f8d; font-size:22px; }}
.vkr-rail .item.active {{ background:#e9f3ff; color:var(--vkr-blue); }}
.vkr-breadcrumb {{ display:flex; align-items:center; gap:12px; color:#6f7d96; font-size:15px; font-weight:650; margin: 8px 0 22px; }}
.vkr-breadcrumb .active {{ color: var(--vkr-blue); }}
.vkr-page-card {{
  background:white; border:1px solid var(--vkr-border); border-radius:16px;
  box-shadow: 0 8px 30px rgba(21, 52, 92, .06); overflow:hidden;
}}
.vkr-page-title {{
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding: 22px 28px; border-bottom:1px solid var(--vkr-border);
}}
.vkr-page-title h1 {{ font-size:26px; line-height:1.15; margin:0; color:var(--vkr-text); }}
.vkr-actions {{ display:flex; align-items:center; gap:16px; color:#5f6f8d; font-weight:650; }}
.vkr-content {{ padding: 22px 26px; }}
.vkr-hero {{
  display:flex; align-items:center; justify-content:space-between; gap:24px;
  padding:26px; border:1px solid var(--vkr-border); border-radius:16px; background:white;
}}
.vkr-hero-left {{ display:flex; align-items:center; gap:22px; }}
.vkr-big-icon {{ width:74px; height:74px; border-radius:50%; background:linear-gradient(135deg,#0d6bdc,#084a9e); color:white; display:flex; align-items:center; justify-content:center; font-size:36px; flex:0 0 auto; box-shadow: 0 9px 22px rgba(13, 107, 220, .20); }}
.vkr-hero h2 {{ margin:0 0 9px 0; font-size:28px; color:var(--vkr-text); }}
.vkr-subtitle {{ color:#61718d; font-size:17px; font-weight:650; }}
.vkr-badge {{ padding:17px 22px; border-radius:14px; font-size:19px; font-weight:800; white-space:nowrap; display:flex; align-items:center; gap:12px; }}
.vkr-badge.danger {{ color:#ef2e2e; background:#fff2f2; border:1px solid #ffc9c9; }}
.vkr-badge.warning {{ color:#af6a00; background:#fff7e6; border:1px solid #ffe0a3; }}
.vkr-badge.success {{ color:#168447; background:#eefbf4; border:1px solid #bfead2; }}
.vkr-grid-3 {{ display:grid; grid-template-columns: 1.05fr 1.05fr .9fr; gap:20px; margin-top:22px; }}
.vkr-grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-top:22px; }}
.vkr-card {{ border:1px solid var(--vkr-border); border-radius:16px; background:white; padding:22px; box-shadow:0 6px 18px rgba(21,52,92,.04); }}
.vkr-card h3 {{ margin:0 0 16px; font-size:21px; color:var(--vkr-text); display:flex; align-items:center; gap:11px; }}
.vkr-card p {{ color:#4f5e77; font-size:16px; line-height:1.55; }}
.vkr-kpi-grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; }}
.vkr-kpi {{ border:1px solid var(--vkr-border); border-radius:13px; padding:14px 12px; min-height:74px; display:flex; gap:12px; align-items:center; background:#fbfdff; }}
.vkr-kpi .num {{ font-size:28px; font-weight:850; color:var(--vkr-blue); line-height:1; }}
.vkr-kpi .label {{ font-size:13px; color:#5f6f8d; line-height:1.15; font-weight:650; }}
.vkr-entity {{ display:flex; align-items:center; gap:12px; margin:13px 0; font-size:17px; color:#3f4f6b; font-weight:650; }}
.vkr-entity .eicon {{ color:var(--vkr-blue); width:24px; text-align:center; }}
.vkr-list-item {{ border:1px solid var(--vkr-border); border-radius:12px; padding:14px 16px; margin:10px 0; color:#3f4f6b; font-weight:650; background:#fbfdff; display:flex; gap:12px; align-items:flex-start; }}
.vkr-list-item .bullet {{ color:var(--vkr-blue); font-size:19px; line-height:1.1; }}
.vkr-network {{ position:relative; height: 330px; border-radius:14px; background:linear-gradient(180deg,#fbfdff,#ffffff); overflow:hidden; }}
.vkr-line {{ position:absolute; height:2px; background:#aab9d0; transform-origin:left center; opacity:.75; }}
.vkr-node {{ position:absolute; width:92px; height:92px; margin-left:-46px; margin-top:-46px; border-radius:50%; display:flex; align-items:center; justify-content:center; text-align:center; padding:10px; font-size:12px; line-height:1.15; font-weight:760; }}
.vkr-node.green {{ background:#95ed9f; border:2px solid #53c96b; color:#123622; }}
.vkr-node.blue {{ background:#eaf4ff; border:2px solid #79b3ff; color:#12345f; }}
.vkr-node.center {{ width:116px; height:116px; margin-left:-58px; margin-top:-58px; background:#6ee789; border:3px solid #2fba55; font-size:14px; color:#0f3920; }}
.vkr-assistant-shell {{ display:grid; grid-template-columns: 230px 1fr; gap:28px; max-width: 1040px; margin: 0 auto; padding: 22px 0; }}
.vkr-assistant-panel {{ background: linear-gradient(180deg,#eff7ff,#f8fbff); border:1px solid #cfe0f5; border-radius:16px; padding:18px; }}
.vkr-assistant-panel h3 {{ margin:0 0 16px; color:var(--vkr-text); }}
.vkr-input-label {{ color:#34445f; font-size:13px; font-weight:760; margin:15px 0 7px; }}
.vkr-fake-input {{ background:white; border:1px solid #dbe6f5; border-radius:8px; padding:10px 12px; color:#4f5e77; font-size:13px; }}
.vkr-primary-btn {{ background:linear-gradient(135deg,#0d6bdc,#0857b4); color:white; border-radius:9px; padding:12px 14px; text-align:center; font-weight:800; margin-top:62px; box-shadow:0 9px 20px rgba(13,107,220,.22); }}
.vkr-chat-title {{ font-size:23px; font-weight:850; margin:6px 0 8px; color:var(--vkr-text); }}
.vkr-chat-subtitle {{ color:#687890; font-size:14px; margin-bottom:18px; }}
.vkr-msg {{ display:flex; gap:14px; align-items:flex-start; margin:14px 0; }}
.vkr-avatar {{ width:34px; height:34px; border-radius:50%; background:#e5f2ff; color:var(--vkr-blue); display:flex; align-items:center; justify-content:center; flex:0 0 auto; border:1px solid #a9d0ff; }}
.vkr-avatar.bot {{ background:#075bb4; color:white; border-color:#075bb4; }}
.vkr-bubble {{ border:1px solid #cfe0f5; background:#edf6ff; padding:13px 16px; border-radius:12px; color:#30415c; width:100%; font-weight:650; }}
.vkr-answer {{ border:1px solid #d8e5f4; border-radius:12px; padding:16px; background:white; width:100%; }}
.vkr-answer h3 {{ margin:0 0 14px; color:var(--vkr-text); }}
.vkr-problem-row {{ display:grid; grid-template-columns:40px 1fr 160px; gap:12px; align-items:center; border:1px solid #dbe6f5; border-radius:9px; padding:10px 12px; margin:8px 0; background:#fbfdff; }}
.vkr-rank {{ width:29px; height:29px; border-radius:8px; display:flex; align-items:center; justify-content:center; background:#e9f3ff; color:var(--vkr-blue); font-weight:850; }}
.vkr-row-title {{ font-weight:850; color:#263856; font-size:14px; }}
.vkr-row-desc {{ color:#687890; font-size:12px; margin-top:2px; }}
.vkr-link {{ color:var(--vkr-blue); font-weight:750; font-size:13px; text-align:right; }}
.vkr-footnote {{ display:flex; gap:10px; align-items:center; margin-top:14px; color:#65758f; font-size:12px; }}
.vkr-refresh {{ display:flex; justify-content:space-between; align-items:center; border:1px solid var(--vkr-border); border-radius:14px; padding:13px 18px; color:#61718d; font-weight:650; margin-top:22px; }}
@media (max-width: 1150px) {{
  .block-container {{ padding-left: 1.2rem !important; padding-right: 1.2rem !important; }}
  .vkr-topbar {{ margin-left: -1.2rem; margin-right: -1.2rem; }}
  .vkr-rail {{ display:none; }}
  .vkr-grid-3, .vkr-grid-2, .vkr-assistant-shell {{ grid-template-columns:1fr; }}
  .vkr-nav {{ display:none; }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(active: str = "Анализ проблем") -> None:
    nav = ["Анализ проблем", "Обращения", "Сущности", "Отчёты", "Карта"]
    parts = []
    for n in nav:
        cls = "active" if n == active else ""
        parts.append(f'<span class="{cls}">{esc(n)}</span>')
    nav_html = "".join(parts)
    st.markdown(
        f"""
<div class="vkr-topbar">
  <div class="vkr-brand"><div class="vkr-logo">▦</div><span>Аналитическая платформа</span></div>
  <div class="vkr-nav">{nav_html}</div>
  <div class="vkr-icons"><span>♡</span><span>?</span><span>◉</span><span>⌄</span></div>
</div>
<div class="vkr-rail">
  <div class="item">▦</div><div class="item active">⌁</div><div class="item">▱</div><div class="item">⌖</div>
  <div class="item">▥</div><div class="item">♙</div><div class="item">▤</div><div class="item">⚙</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_breadcrumb(current: str) -> None:
    st.markdown(
        f"""
<div class="vkr-breadcrumb">
  <span>⌂</span><span>›</span><span>Анализ проблем</span><span>›</span><span>Комплексные проблемы</span><span>›</span><span class="active">{esc(current)}</span>
</div>
        """,
        unsafe_allow_html=True,
    )


def candidate_title(candidate: Dict[str, Any]) -> str:
    return str(candidate.get("title") or candidate.get("Проблема") or "Комплексная городская проблема")


def candidate_score(candidate: Dict[str, Any]) -> float:
    return float(candidate.get("complexity_score") or candidate.get("Complexity_score") or 0.0)


def candidate_metrics(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return candidate.get("metrics", {}) or {}


def summary_text(candidate: Dict[str, Any]) -> str:
    summary = candidate.get("llm_summary") or {}
    text = summary.get("problem_essence") or "Кандидат комплексной проблемы сформирован на основе группы связанных обращений, сущностей, действий и проблемных признаков."
    why = summary.get("why_complex") or "Индекс комплексности рассчитан по частоте обращений, числу связей, разнообразию сущностей и плотности локального подграфа."
    return f"<p>{esc(text)}</p><p>{esc(why)}</p>"


def short_label(value: Any, max_len: int = 24) -> str:
    s = str(value or "").strip()
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def render_network(candidate: Dict[str, Any]) -> None:
    entities = [x for x in (candidate.get("entities") or []) if x]
    actors = [x for x in (candidate.get("actors") or []) if x]
    anchors = [x for x in (candidate.get("problem_anchors") or []) if x]
    center = short_label((candidate.get("problem_type") or entities[0] if entities else candidate_title(candidate)), 18)
    nodes = []
    for name in (entities[:3] + actors[:2] + anchors[:1]):
        if name not in nodes:
            nodes.append(name)
    if len(nodes) < 5:
        nodes += ["жители", "территория", "исполнитель", "обращения"][: 5 - len(nodes)]
    nodes = nodes[:6]
    cx, cy = 50, 52
    radius_x, radius_y = 33, 34
    line_html = []
    node_html = [f'<div class="vkr-node center" style="left:{cx}%;top:{cy}%">{esc(center)}</div>']
    for i, name in enumerate(nodes):
        angle = 2 * math.pi * i / len(nodes) - math.pi / 2
        x = cx + radius_x * math.cos(angle)
        y = cy + radius_y * math.sin(angle)
        dx, dy = x - cx, y - cy
        length = math.sqrt(dx * dx + dy * dy)
        angle_deg = math.degrees(math.atan2(dy, dx))
        line_html.append(f'<div class="vkr-line" style="left:{cx}%;top:{cy}%;width:{length}%;transform:rotate({angle_deg}deg)"></div>')
        color = "green" if i < 4 else "blue"
        node_html.append(f'<div class="vkr-node {color}" style="left:{x}%;top:{y}%">{esc(short_label(name, 18))}</div>')
    st.markdown(f'<div class="vkr-network">{"".join(line_html)}{"".join(node_html)}</div>', unsafe_allow_html=True)


def render_problem_card_page(candidate: Dict[str, Any], region: str = "Санкт-Петербург") -> None:
    title = candidate_title(candidate)
    score = candidate_score(candidate)
    level, level_cls = score_level(score)
    metrics = candidate_metrics(candidate)
    period = candidate.get("time_window") or {}
    date_text = period.get("start") or period.get("end") or "2022"
    entities = candidate.get("entities") or []
    actors = candidate.get("actors") or []
    territories = candidate.get("territories") or []
    actions = candidate.get("actions") or []
    anchors = candidate.get("problem_anchors") or []
    evidence = candidate.get("evidence_appeals") or []
    summary = candidate.get("llm_summary") or {}
    recommendations = summary.get("management_actions") or [
        "проверить подтверждающие обращения и адреса",
        "назначить владельца проблемы",
        "синхронизировать действия ответственных исполнителей",
        "контролировать сроки устранения причины повторяемости",
    ]
    risks = summary.get("risks") or [
        "повторяемость обращений на одной территории",
        "несогласованность действий исполнителей",
        "недостаточное информирование жителей",
    ]

    render_breadcrumb("Карточка проблемы")
    st.markdown('<div class="vkr-page-card">', unsafe_allow_html=True)
    st.markdown(
        """
<div class="vkr-page-title">
  <h1>Карточка комплексной городской проблемы</h1>
  <div class="vkr-actions"><span>▱ Сохранить</span><span>⇧ Экспортировать</span><span>•••</span></div>
</div>
<div class="vkr-content">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="vkr-hero">
  <div class="vkr-hero-left">
    <div class="vkr-big-icon">▥</div>
    <div><h2>{esc(title)}</h2><div class="vkr-subtitle">{esc(region)} · {esc(date_text)}</div></div>
  </div>
  <div class="vkr-badge {level_cls}">⌁ Индекс комплексности: {score:.2f} · {esc(level)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="vkr-grid-3">', unsafe_allow_html=True)
    st.markdown(f'<div class="vkr-card"><h3>▤ Краткое описание</h3>{summary_text(candidate)}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="vkr-card"><h3>▥ Признаки комплексности</h3>
  <div class="vkr-kpi-grid">
    <div class="vkr-kpi"><div class="num">{int(metrics.get('frequency') or len(candidate.get('appeal_ids', [])) or 0)}</div><div class="label">обращений</div></div>
    <div class="vkr-kpi"><div class="num">{len(actors) or int(metrics.get('unique_actors') or 0)}</div><div class="label">акторов</div></div>
    <div class="vkr-kpi"><div class="num">{len(territories)}</div><div class="label">адреса</div></div>
    <div class="vkr-kpi"><div class="num">{len(set(actions))}</div><div class="label">действия</div></div>
    <div class="vkr-kpi"><div class="num">{int(metrics.get('relations_count') or 0)}</div><div class="label">связи</div></div>
    <div class="vkr-kpi"><div class="num">{len(candidate.get('thematic_areas') or []) or 1}</div><div class="label">тематические области</div></div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    key_entities = (entities[:5] or anchors[:5] or [title])
    ent_html = "".join([f'<div class="vkr-entity"><span class="eicon">{icon}</span><span>{esc(short_label(name, 42))}</span></div>' for icon, name in zip(["▥", "▦", "⌘", "♙", "⌁"], key_entities)])
    st.markdown(f'<div class="vkr-card"><h3>◇ Ключевые сущности</h3>{ent_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vkr-grid-2">', unsafe_allow_html=True)
    st.markdown('<div class="vkr-card"><h3>⌘ Связи между сущностями</h3>', unsafe_allow_html=True)
    render_network(candidate)
    st.markdown('</div>', unsafe_allow_html=True)
    evidence_html = ""
    if evidence:
        for ev in evidence[:4]:
            address = ev.get("address") or ev.get("date") or ev.get("appeal_id")
            text = short_label(ev.get("text"), 120)
            evidence_html += f'<div class="vkr-list-item"><span class="bullet">▱</span><span>{esc(address)} — {esc(text)}</span></div>'
    else:
        evidence_html = '<div class="vkr-list-item"><span class="bullet">▱</span><span>Для подтверждающих обращений нужен JSONL-артефакт problem_candidates.jsonl.</span></div>'
    st.markdown(f'<div class="vkr-card"><h3>▱ Подтверждающие обращения</h3>{evidence_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vkr-grid-2">', unsafe_allow_html=True)
    risks_html = "".join([f"<li>{esc(x)}</li>" for x in risks[:5]])
    rec_html = "".join([f"<li>{esc(x)}</li>" for x in recommendations[:5]])
    st.markdown(f'<div class="vkr-card"><h3>△ Возможные причины</h3><ul>{risks_html}</ul></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="vkr-card"><h3>○ Рекомендуемые действия</h3><ul>{rec_html}</ul></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="vkr-refresh"><span>ⓘ Данные сформированы на основе расчетных артефактов пайплайна</span><span>↻ Обновить данные</span></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_assistant_page(candidates: List[Dict[str, Any]], chat_answer: str | None = None) -> None:
    top = candidates[:5]
    rows = []
    for i, c in enumerate(top, 1):
        title = candidate_title(c)
        summary = (c.get("llm_summary") or {}).get("problem_essence") or ", ".join((c.get("problem_anchors") or [])[:2]) or f"Индекс комплексности {candidate_score(c):.2f}"
        rows.append(
            f"""
<div class="vkr-problem-row">
  <div class="vkr-rank">{i}</div>
  <div><div class="vkr-row-title">{esc(short_label(title, 72))}</div><div class="vkr-row-desc">{esc(short_label(summary, 104))}</div></div>
  <div class="vkr-link">Открыть карточку →</div>
</div>
            """
        )
    rows_html = "".join(rows)
    st.markdown('<div class="vkr-page-card"><div class="vkr-content">', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="vkr-assistant-shell">
  <div class="vkr-assistant-panel">
    <h3>Параметры анализа</h3>
    <div class="vkr-input-label">Источник данных</div><div class="vkr-fake-input">ЦУР + платформы</div>
    <div class="vkr-input-label">Период</div><div class="vkr-fake-input">2022 год</div>
    <div class="vkr-input-label">Регион</div><div class="vkr-fake-input">Санкт-Петербург</div>
    <div class="vkr-input-label">Фильтр</div><div class="vkr-fake-input">Все категории</div>
    <div class="vkr-primary-btn">Запустить анализ</div>
  </div>
  <div>
    <div class="vkr-chat-title">Интерфейс ИИ-помощника для анализа комплексных городских проблем</div>
    <div class="vkr-chat-subtitle">Модуль получает результаты графового анализа и помогает выявить наиболее значимые комплексные проблемы города.</div>
    <div class="vkr-msg"><div class="vkr-avatar">☻</div><div class="vkr-bubble">Какие комплексные проблемы ты видишь в городе?</div></div>
    <div class="vkr-msg"><div class="vkr-avatar bot">✦</div><div class="vkr-answer"><h3>Топ-5 комплексных проблем</h3>{rows_html}<div class="vkr-footnote">ⓘ Выберите проблему, чтобы перейти к подробной карточке с метриками, обращениями, рисками и рекомендуемыми действиями.</div></div></div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    if chat_answer:
        st.markdown(f'<div class="vkr-card"><h3>Ответ ИИ-помощника</h3><p>{esc(chat_answer)}</p></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
