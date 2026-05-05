from __future__ import annotations

import html
import math
from typing import Any, Dict, Iterable, List

import streamlit as st

BLUE = "#0b63ce"
BLUE_DARK = "#083f86"
BORDER = "#d8e6f7"
TEXT = "#0b1b35"
MUTED = "#66758f"
BG = "#f6f9fe"


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def candidate_title(candidate: Dict[str, Any]) -> str:
    return str(candidate.get("title") or candidate.get("Проблема") or "Комплексная городская проблема")


def candidate_score(candidate: Dict[str, Any]) -> float:
    try:
        return float(candidate.get("complexity_score") or candidate.get("Complexity_score") or 0.0)
    except Exception:
        return 0.0


def candidate_metrics(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return candidate.get("metrics", {}) or {}


def candidate_frequency(candidate: Dict[str, Any]) -> int:
    metrics = candidate_metrics(candidate)
    return int(metrics.get("frequency") or len(candidate.get("appeal_ids", [])) or candidate.get("Частота_упоминаний") or 0)


def score_level(score: float) -> tuple[str, str]:
    if score >= 0.70:
        return "высокий", "danger"
    if score >= 0.45:
        return "средний", "warning"
    return "умеренный", "success"


def first_non_empty(values: Iterable[Any], fallback: str = "—") -> str:
    for value in values:
        if value:
            return str(value)
    return fallback


def short(value: Any, max_len: int = 95) -> str:
    text = str(value or "").strip().replace("\n", " ")
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


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
#MainMenu, footer, header {{visibility:hidden;}}
.stApp {{ background: linear-gradient(180deg, #fbfdff 0%, #f6f9fe 100%); }}
.block-container {{
  max-width: 1180px !important;
  padding-top: 0.6rem !important;
  padding-bottom: 2.5rem !important;
}}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #eef6ff 0%, #f9fcff 100%);
  border-right: 1px solid var(--vkr-border);
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: var(--vkr-text); }}
[data-testid="stSidebar"] .stButton > button {{
  background: linear-gradient(135deg,#0d6bdc,#0857b4) !important;
  color: white !important;
  border: none !important;
  box-shadow: 0 10px 24px rgba(13,107,220,.20) !important;
  min-height: 48px !important;
  font-weight: 850 !important;
}}
.stButton > button, .stDownloadButton > button {{
  border-radius: 11px !important;
  border: 1px solid #cfe0f5 !important;
  min-height: 39px !important;
  font-weight: 760 !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: var(--vkr-blue) !important; color: var(--vkr-blue) !important; }}
.vkr-topbar {{
  height: 64px;
  border-bottom: 1px solid var(--vkr-border);
  background: rgba(255,255,255,.96);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: -0.6rem calc(-50vw + 50%) 1.4rem calc(-50vw + 50%);
  padding: 0 max(24px, calc((100vw - 1180px)/2));
  position: sticky;
  top: 0;
  z-index: 30;
  box-shadow: 0 4px 18px rgba(18,45,82,.05);
}}
.vkr-brand {{ display:flex; align-items:center; gap:13px; font-weight:850; font-size:19px; color:var(--vkr-text); }}
.vkr-logo {{
  width:38px; height:38px; border-radius:10px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,#0d6bdc,#084a9e);
  color:white; font-size:21px; box-shadow:0 7px 16px rgba(13,107,220,.24);
}}
.vkr-single-nav {{ color:var(--vkr-blue); font-weight:850; border-bottom:3px solid var(--vkr-blue); padding:22px 8px 17px; }}
.vkr-clean-title {{ margin: 18px 0 8px; color: var(--vkr-text); font-size: 27px; line-height: 1.25; font-weight: 900; }}
.vkr-subtitle {{ color:#66758f; font-size:14px; margin-bottom:20px; }}
.vkr-side-note {{ color:#536784; font-size:13px; line-height:1.45; margin: 10px 0 6px; }}
.vkr-chat-wrap {{ max-width: 900px; margin: 0 auto; }}
.vkr-soft-question {{
  border:1px solid #bdd9ff;
  background:#ecf6ff;
  border-radius:14px;
  padding:14px 18px;
  color:#263856;
  font-weight:760;
  margin: 8px 0 14px;
}}
.vkr-dialog-list {{
  border:1px solid #d8e5f4;
  border-radius:15px;
  padding:16px 16px 8px;
  background:white;
  box-shadow:0 8px 26px rgba(21,52,92,.05);
}}
.vkr-dialog-list h3 {{ margin:0 0 14px; color:var(--vkr-text); font-size:23px; }}
.vkr-problem-card {{
  border:1px solid #dbe7f7;
  background:#fbfdff;
  border-radius:13px;
  padding:13px 14px;
  margin-bottom:10px;
}}
.vkr-problem-title {{ font-size:14px; font-weight:900; color:#172a48; margin-bottom:5px; }}
.vkr-problem-desc {{ font-size:12px; color:#63748f; line-height:1.45; }}
.vkr-rank {{
  width:30px; height:30px; border-radius:9px;
  background:#e9f3ff; color:var(--vkr-blue);
  font-weight:900; display:flex; align-items:center; justify-content:center;
}}
.vkr-kpi-row {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin:18px 0; }}
.vkr-kpi {{ background:#fff; border:1px solid var(--vkr-border); border-radius:14px; padding:14px 15px; box-shadow:0 8px 24px rgba(21,52,92,.04); }}
.vkr-kpi .num {{ font-size:28px; font-weight:900; color:var(--vkr-blue); line-height:1; }}
.vkr-kpi .label {{ color:#60718d; font-size:13px; font-weight:700; margin-top:4px; }}
.vkr-card-shell {{ background:white; border:1px solid var(--vkr-border); border-radius:18px; padding:24px; box-shadow:0 10px 35px rgba(21,52,92,.05); }}
.vkr-card-head {{ display:flex; justify-content:space-between; gap:24px; align-items:center; border:1px solid var(--vkr-border); border-radius:17px; padding:22px; background:#fbfdff; margin-bottom:18px; }}
.vkr-card-head h1 {{ margin:0 0 8px; font-size:28px; color:var(--vkr-text); line-height:1.18; }}
.vkr-chip {{ display:inline-flex; align-items:center; gap:8px; border-radius:14px; padding:13px 18px; font-weight:900; white-space:nowrap; }}
.vkr-chip.danger {{ color:#e02020; background:#fff1f1; border:1px solid #ffc8c8; }}
.vkr-chip.warning {{ color:#a66a00; background:#fff8e7; border:1px solid #ffe0a3; }}
.vkr-chip.success {{ color:#14723b; background:#ecfff3; border:1px solid #bcebcf; }}
.vkr-section {{ background:#fff; border:1px solid var(--vkr-border); border-radius:16px; padding:18px; margin-bottom:16px; }}
.vkr-section h3 {{ margin:0 0 12px; color:var(--vkr-text); font-size:19px; }}
.vkr-section p {{ color:#4f5e77; font-size:15px; line-height:1.55; }}
.vkr-list-item {{ border:1px solid #dbe6f5; border-radius:12px; padding:12px 14px; margin:8px 0; color:#3f4f6b; font-weight:650; background:#fbfdff; display:flex; gap:10px; align-items:flex-start; }}
.vkr-list-item .bullet {{ color:var(--vkr-blue); font-weight:900; }}
.vkr-entity {{ display:flex; align-items:center; gap:11px; margin:11px 0; color:#3f4f6b; font-weight:750; }}
.vkr-entity .eicon {{ color:var(--vkr-blue); width:24px; text-align:center; }}
.vkr-network {{ position:relative; height:320px; border:1px solid #e3ecf7; border-radius:14px; background:linear-gradient(180deg,#fbfdff,#fff); overflow:hidden; }}
.vkr-line {{ position:absolute; height:2px; background:#aab9d0; transform-origin:left center; opacity:.75; }}
.vkr-node {{ position:absolute; width:86px; height:86px; margin-left:-43px; margin-top:-43px; border-radius:50%; display:flex; align-items:center; justify-content:center; text-align:center; padding:9px; font-size:11px; line-height:1.15; font-weight:800; }}
.vkr-node.green {{ background:#96efa0; border:2px solid #53c96b; color:#123622; }}
.vkr-node.blue {{ background:#eaf4ff; border:2px solid #79b3ff; color:#12345f; }}
.vkr-node.center {{ width:112px; height:112px; margin-left:-56px; margin-top:-56px; background:#6ee789; border:3px solid #2fba55; font-size:13px; color:#0f3920; }}
.vkr-muted {{ color:#687890; }}
@media (max-width: 900px) {{
  .block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
  .vkr-topbar {{ padding-left: 1rem; padding-right: 1rem; }}
  .vkr-kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  .vkr-card-head {{ flex-direction:column; align-items:flex-start; }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    st.markdown(
        """
<div class="vkr-topbar">
  <div class="vkr-brand"><div class="vkr-logo">▦</div><span>Аналитическая платформа</span></div>
  <div class="vkr-single-nav">Анализ проблем</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_problem_preview(candidate: Dict[str, Any], rank: int) -> None:
    summary = candidate.get("llm_summary") or {}
    desc = summary.get("problem_essence") or "Проблема выявлена на основе повторяющихся обращений, сущностей и связей."
    st.markdown(
        f"""
<div class="vkr-problem-card">
  <div style="display:grid;grid-template-columns:40px 1fr;gap:12px;align-items:start;">
    <div class="vkr-rank">{rank}</div>
    <div>
      <div class="vkr-problem-title">{esc(candidate_title(candidate))}</div>
      <div class="vkr-problem-desc">{esc(short(desc, 170))}</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_dialog_intro(candidates: List[Dict[str, Any]]) -> None:
    st.markdown('<div class="vkr-soft-question">Какие комплексные проблемы ты видишь в городе?</div>', unsafe_allow_html=True)
    st.markdown('<div class="vkr-dialog-list"><h3>Топ-5 комплексных проблем</h3>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_kpi_row(candidate: Dict[str, Any]) -> None:
    metrics = candidate_metrics(candidate)
    actors = candidate.get("actors") or []
    territories = candidate.get("territories") or []
    thematic = candidate.get("thematic_areas") or []
    html_block = f"""
<div class="vkr-kpi-row">
  <div class="vkr-kpi"><div class="num">{candidate_frequency(candidate)}</div><div class="label">обращений</div></div>
  <div class="vkr-kpi"><div class="num">{len(actors)}</div><div class="label">типов заявителей / акторов</div></div>
  <div class="vkr-kpi"><div class="num">{len(territories)}</div><div class="label">адресов / территорий</div></div>
  <div class="vkr-kpi"><div class="num">{metrics.get('relations_count', 0)}</div><div class="label">связей</div></div>
</div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def render_network(candidate: Dict[str, Any]) -> None:
    entities = [x for x in (candidate.get("entities") or []) if x]
    actors = [x for x in (candidate.get("actors") or []) if x]
    anchors = [x for x in (candidate.get("problem_anchors") or []) if x]
    center = short(candidate.get("problem_type") or (entities[0] if entities else candidate_title(candidate)), 18)
    nodes: List[str] = []
    for value in entities[:3] + actors[:2] + anchors[:1]:
        if value and value not in nodes:
            nodes.append(value)
    if len(nodes) < 5:
        nodes += ["жители", "территория", "исполнитель", "обращения"][: 5 - len(nodes)]
    nodes = nodes[:6]
    cx, cy = 50, 52
    rx, ry = 33, 33
    lines: List[str] = []
    node_html = [f'<div class="vkr-node center" style="left:{cx}%;top:{cy}%">{esc(center)}</div>']
    for i, name in enumerate(nodes):
        angle = 2 * math.pi * i / len(nodes) - math.pi / 2
        x = cx + rx * math.cos(angle)
        y = cy + ry * math.sin(angle)
        dx, dy = x - cx, y - cy
        length = math.sqrt(dx * dx + dy * dy)
        angle_deg = math.degrees(math.atan2(dy, dx))
        lines.append(f'<div class="vkr-line" style="left:{cx}%;top:{cy}%;width:{length}%;transform:rotate({angle_deg}deg)"></div>')
        color = "green" if i < 4 else "blue"
        node_html.append(f'<div class="vkr-node {color}" style="left:{x}%;top:{y}%">{esc(short(name, 17))}</div>')
    st.markdown(f'<div class="vkr-network">{"".join(lines)}{"".join(node_html)}</div>', unsafe_allow_html=True)


def render_problem_card(candidate: Dict[str, Any], region: str = "Санкт-Петербург") -> None:
    title = candidate_title(candidate)
    score = candidate_score(candidate)
    level, cls = score_level(score)
    period = candidate.get("time_window") or {}
    date_text = period.get("start") or period.get("end") or "2022"
    summary = candidate.get("llm_summary") or {}
    entities = candidate.get("entities") or []
    actions = candidate.get("actions") or []
    anchors = candidate.get("problem_anchors") or []
    evidence = candidate.get("evidence_appeals") or []

    st.markdown('<div class="vkr-card-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="vkr-card-head">
  <div>
    <h1>{esc(title)}</h1>
    <div class="vkr-muted">{esc(region)} · {esc(date_text)}</div>
  </div>
  <div class="vkr-chip {cls}">↗ Индекс комплексности: {score:.2f} · {esc(level)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    render_kpi_row(candidate)

    c1, c2 = st.columns([1.05, 1])
    with c1:
        st.markdown(
            f"""
<div class="vkr-section">
  <h3>Краткое описание</h3>
  <p>{esc(summary.get('problem_essence') or 'Кандидат комплексной проблемы сформирован на основе повторяющихся обращений и связанных сущностей.')}</p>
  <p>{esc(summary.get('why_complex') or 'Комплексность определяется частотой обращений, количеством связей, разнообразием сущностей и плотностью подграфа.')}</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div class="vkr-section"><h3>Ключевые сущности</h3>', unsafe_allow_html=True)
        for entity in entities[:7]:
            st.markdown(f'<div class="vkr-entity"><span class="eicon">◇</span>{esc(entity)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    c3, c4 = st.columns([1.05, 1])
    with c3:
        st.markdown('<div class="vkr-section"><h3>Связи между сущностями</h3>', unsafe_allow_html=True)
        render_network(candidate)
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="vkr-section"><h3>Подтверждающие обращения</h3>', unsafe_allow_html=True)
        if evidence:
            for ev in evidence[:4]:
                line = f"{ev.get('address') or ev.get('appeal_id') or ''} — {short(ev.get('text'), 120)}"
                st.markdown(f'<div class="vkr-list-item"><span class="bullet">▣</span>{esc(line)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p>Примеры обращений доступны при загрузке JSONL-артефакта.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="vkr-section"><h3>Признаки комплексности</h3>', unsafe_allow_html=True)
        for item in (anchors[:4] + actions[:3])[:6]:
            st.markdown(f'<div class="vkr-list-item"><span class="bullet">•</span>{esc(item)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    c5, c6 = st.columns(2)
    risks = summary.get("risks") or ["повторяемость обращений", "размывание ответственности", "рост социальной напряженности"]
    actions_rec = summary.get("management_actions") or ["проверить подтверждающие обращения", "назначить владельца проблемы", "согласовать ответственных исполнителей"]
    with c5:
        st.markdown('<div class="vkr-section"><h3>Возможные причины</h3>', unsafe_allow_html=True)
        for item in risks[:5]:
            st.markdown(f'<div class="vkr-list-item"><span class="bullet">•</span>{esc(item)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c6:
        st.markdown('<div class="vkr-section"><h3>Рекомендуемые действия</h3>', unsafe_allow_html=True)
        for item in actions_rec[:5]:
            st.markdown(f'<div class="vkr-list-item"><span class="bullet">✓</span>{esc(item)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
