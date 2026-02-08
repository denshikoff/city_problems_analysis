from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import math


@dataclass(frozen=True)
class CalibrationConfig:
    """
    Калибровка под реальные городские данные.
    scale_* задают "характерный масштаб" для мягкой нормализации:
    score_component = 1 - exp(-value / scale)
    """
    scale_frequency: float = 120.0          # типичные частоты 50..300
    scale_unique_entities: float = 60.0     # типично 10..150
    scale_unique_actions: float = 40.0      # типично 5..150
    scale_relations_count: float = 120.0    # типично 20..300

    # плотность графа в [0..1], но реальная часто 0.01..0.4
    density_min: float = 0.01
    density_max: float = 0.40

    # штрафы/бонусы
    min_actions_for_systemic: int = 2
    min_entities_for_systemic: int = 3
    penalty_if_too_simple: float = 0.15     # если слишком мало акторов/действий — вниз


class ComplexProblemScorer:
    """
    Детерминированная оценка комплексности одной проблемы (0..1),
    откалиброванная на городских данных.

    Вход: метрики конкретной проблемы (объекта) из identify_problems.
    Выход: score 0..1 + разложение факторов для отчёта.
    """

    def __init__(
        self,
        frequency: int,
        unique_entities: int,
        unique_actions: int,
        subgraph_density: float,
        relations_count: int,
        *,
        weights: Dict[str, float] | None = None,
        calibration: CalibrationConfig | None = None
    ):
        self.frequency = max(0, int(frequency))
        self.unique_entities = max(0, int(unique_entities))
        self.unique_actions = max(0, int(unique_actions))
        self.subgraph_density = float(subgraph_density) if subgraph_density is not None else 0.0
        self.relations_count = max(0, int(relations_count))

        self.cal = calibration or CalibrationConfig()

        # веса (сумма ≈ 1.0)
        self.w = weights or {
            "frequency": 0.30,
            "entities": 0.25,
            "actions": 0.15,
            "density": 0.15,
            "relations": 0.15
        }

        self._validate_weights()

    def _validate_weights(self) -> None:
        s = sum(self.w.values())
        if s <= 0:
            raise ValueError("weights sum must be > 0")
        # нормализуем, если вдруг не 1.0
        if abs(s - 1.0) > 1e-6:
            self.w = {k: v / s for k, v in self.w.items()}

    @staticmethod
    def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, x))

    @staticmethod
    def _soft_norm(value: float, scale: float) -> float:
        """
        Мягкая нормализация 0..1 без "быстрого насыщения" (но всё же насыщается плавно).
        """
        if scale <= 0:
            return 0.0
        v = max(0.0, float(value))
        return 1.0 - math.exp(-v / scale)

    def _density_norm(self, d: float) -> float:
        """
        Плотность нормализуем линейно в пределах density_min..density_max.
        """
        d = 0.0 if d is None else float(d)
        d = self._clamp(d, 0.0, 1.0)
        a, b = self.cal.density_min, self.cal.density_max
        if b <= a:
            return 0.0
        return self._clamp((d - a) / (b - a), 0.0, 1.0)

    def compute(self) -> float:
        freq_c = self._soft_norm(self.frequency, self.cal.scale_frequency)
        ent_c = self._soft_norm(self.unique_entities, self.cal.scale_unique_entities)
        act_c = self._soft_norm(self.unique_actions, self.cal.scale_unique_actions)
        rel_c = self._soft_norm(self.relations_count, self.cal.scale_relations_count)
        den_c = self._density_norm(self.subgraph_density)

        score = (
            self.w["frequency"] * freq_c +
            self.w["entities"] * ent_c +
            self.w["actions"] * act_c +
            self.w["relations"] * rel_c +
            self.w["density"] * den_c
        )

        # Штраф за "слишком простые" случаи (чтобы не считались комплексными)
        if (self.unique_actions < self.cal.min_actions_for_systemic) or (
            self.unique_entities < self.cal.min_entities_for_systemic
        ):
            score = score * (1.0 - self.cal.penalty_if_too_simple)

        return round(self._clamp(score), 3)

    def explain(self) -> Dict[str, Any]:
        """
        Разложение на компоненты для отчёта/валидации.
        """
        freq_c = self._soft_norm(self.frequency, self.cal.scale_frequency)
        ent_c = self._soft_norm(self.unique_entities, self.cal.scale_unique_entities)
        act_c = self._soft_norm(self.unique_actions, self.cal.scale_unique_actions)
        rel_c = self._soft_norm(self.relations_count, self.cal.scale_relations_count)
        den_c = self._density_norm(self.subgraph_density)

        base = {
            "frequency_component": round(freq_c, 3),
            "entities_component": round(ent_c, 3),
            "actions_component": round(act_c, 3),
            "relations_component": round(rel_c, 3),
            "density_component": round(den_c, 3),
            "weights": dict(self.w),
            "raw": {
                "frequency": self.frequency,
                "unique_entities": self.unique_entities,
                "unique_actions": self.unique_actions,
                "relations_count": self.relations_count,
                "subgraph_density": round(float(self.subgraph_density), 6),
            },
            "penalty_applied": bool(
                (self.unique_actions < self.cal.min_actions_for_systemic) or
                (self.unique_entities < self.cal.min_entities_for_systemic)
            )
        }

        # итог
        base["complexity_score"] = self.compute()
        return base
