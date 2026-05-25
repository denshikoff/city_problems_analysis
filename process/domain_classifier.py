"""Классификация обращений по городским сферам.

Используется для признака межсферности комплексной проблемы:
одна и та же проблемная группа может затрагивать дороги, ЖКХ,
транспорт, благоустройство и другие сферы.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import re


@dataclass(frozen=True)
class DomainRule:
    domain: str
    keywords: tuple[str, ...]


DOMAIN_RULES: tuple[DomainRule, ...] = (
    DomainRule("Дороги", ("дорог", "асфальт", "проезж", "тротуар", "яма", "выбоин", "светофор", "разметк")),
    DomainRule("Транспорт", ("транспорт", "автобус", "трамвай", "троллейбус", "маршрут", "останов", "график движения", "расписан")),
    DomainRule("ЖКХ", ("жкх", "отоплен", "водоснаб", "канализа", "подъезд", "лифт", "мкд", "кровл", "крыша", "жку", "электрич", "газ")),
    DomainRule("Благоустройство", ("благоустрой", "двор", "уборк", "снег", "налед", "парк", "сквер", "газон", "площадк")),
    DomainRule("Обращение с отходами", ("мусор", "тко", "контейнер", "свалк", "отход", "помойк")),
    DomainRule("Безопасность", ("безопас", "аварийн", "опасн", "угроз", "травм", "пожар", "освещ", "фонар")),
    DomainRule("Экология", ("эколог", "дерев", "животн", "собак", "воздух", "дым", "зелен")),
    DomainRule("Социальная сфера", ("социаль", "льгот", "выплат", "семь", "ребен", "пособ")),
    DomainRule("Здравоохранение", ("здрав", "медицин", "поликлиник", "врач", "лекар", "больниц")),
    DomainRule("Образование", ("образован", "школ", "детский сад", "доу", "учрежден")),
)


def normalize_text(value: object) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_domains(*parts: object, fallback: str = "Другое") -> list[str]:
    """Возвращает список сфер, найденных в направлении, теме и тексте обращения."""
    text = normalize_text(" ".join(str(p or "") for p in parts))
    domains: list[str] = []
    for rule in DOMAIN_RULES:
        if any(keyword in text for keyword in rule.keywords):
            domains.append(rule.domain)
    return domains or [fallback]


def domain_counts(rows: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for domain in classify_domains(row.get("direction"), row.get("topic"), row.get("text"), fallback=row.get("direction") or "Другое"):
            counts[domain] = counts.get(domain, 0) + 1
    return counts
