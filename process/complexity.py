"""Расчет комплексности городской проблемы.

Новая версия учитывает не только количество стейкхолдеров, но и:
1) пересечение городских сфер: дороги, ЖКХ, транспорт и т.д.;
2) территориальный охват;
3) устойчивость во времени;
4) разнообразие исполнителей/стейкхолдеров;
5) разнообразие требуемых действий;
6) риск/аварийность в текстах обращений.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, log
from typing import Mapping, Sequence


def _soft_cap(value: float, scale: float) -> float:
    """Мягкая нормализация в диапазон 0..1 без жесткого обрезания больших значений."""
    if value <= 0:
        return 0.0
    return 1.0 - exp(-value / scale)


def _entropy_normalized(counts: Mapping[str, int]) -> float:
    total = sum(counts.values())
    if total <= 0 or len(counts) <= 1:
        return 0.0
    entropy = -sum((v / total) * log(v / total) for v in counts.values() if v > 0)
    return entropy / log(len(counts))


@dataclass
class ComplexityFeatures:
    appeals_count: int
    domain_counts: Mapping[str, int] = field(default_factory=dict)
    territory_count: int = 0
    month_count: int = 0
    stakeholder_count: int = 0
    action_count: int = 0
    risk_count: int = 0


@dataclass
class ComplexityResult:
    score: float
    components: dict[str, float]


def compute_complexity(features: ComplexityFeatures) -> ComplexityResult:
    """Считает комплексность в диапазоне 0..1.

    Формула:
    C = 0.22*F + 0.18*S + 0.15*G + 0.15*T + 0.12*A + 0.10*R + 0.08*K

    где:
    F — частотность обращений;
    S — межсферность: число сфер + энтропия распределения по сферам;
    G — территориальный охват;
    T — устойчивость во времени;
    A — разнообразие исполнителей/стейкхолдеров;
    R — разнообразие требуемых действий;
    K — риск/аварийность.
    """
    domain_count = len([v for v in features.domain_counts.values() if v > 0])
    domain_entropy = _entropy_normalized(features.domain_counts)
    cross_domain = 0.0
    if domain_count > 1:
        cross_domain = min(1.0, 0.55 * _soft_cap(domain_count - 1, 1.5) + 0.45 * domain_entropy)

    components = {
        "frequency": _soft_cap(features.appeals_count, 80),
        "cross_domain": cross_domain,
        "territory_spread": _soft_cap(features.territory_count, 15),
        "temporal_persistence": _soft_cap(features.month_count, 4),
        "stakeholder_diversity": _soft_cap(features.stakeholder_count, 8),
        "action_diversity": _soft_cap(features.action_count, 4),
        "risk_signal": min(1.0, (features.risk_count / max(features.appeals_count, 1)) * 1.5),
    }

    score = (
        0.22 * components["frequency"]
        + 0.18 * components["cross_domain"]
        + 0.15 * components["territory_spread"]
        + 0.15 * components["temporal_persistence"]
        + 0.12 * components["stakeholder_diversity"]
        + 0.10 * components["action_diversity"]
        + 0.08 * components["risk_signal"]
    )
    return ComplexityResult(score=round(min(score, 1.0), 3), components={k: round(v, 3) for k, v in components.items()})


def explain_cross_domain(domains: Sequence[str]) -> str:
    unique = sorted(set(d for d in domains if d))
    if len(unique) <= 1:
        return "Проблема относится к одной сфере."
    return "Проблема межсферная: " + ", ".join(unique) + "."
