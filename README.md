# City Problems Analysis

Система анализа обращений граждан для выявления **кандидатов комплексных городских проблем** на основе текстов обращений, графа знаний, индекса комплексности и LLM-интерпретации.

Проект реализует подход, описанный в ВКР: обращение рассматривается не как отдельная жалоба, а как часть связанного проблемного узла городской среды. Алгоритм проходит путь от исходных текстов к сущностям, отношениям, графу знаний, кандидатам комплексных проблем, их ранжированию и представлению в интерфейсе городского ИИ-помощника.

---

## Что делает проект

Проект позволяет:

1. Загружать обращения граждан из `.xlsx`, `.xls` или `.csv`.
2. Очищать и нормализовать тексты обращений.
3. Извлекать городские сущности, действия, акторов, проблемные признаки и связи.
4. Строить граф знаний по обращениям.
5. Выделять кандидаты комплексных городских проблем как связанные фрагменты графа.
6. Рассчитывать `Complexity_score` — индекс комплексности проблемы.
7. Формировать доказательную карточку проблемы:
   - суть проблемы;
   - подтверждающие обращения;
   - ключевые сущности;
   - действия и проблемные признаки;
   - акторов;
   - территории;
   - связи графа;
   - факторы индекса комплексности;
   - LLM/heuristic-сводку.
8. Показывать результаты в Streamlit-интерфейсе городского ИИ-помощника.

---

## Архитектура

```text
city_problems_analysis/
├── process/
│   ├── main.py                    # основной пайплайн обработки
│   ├── clean_proceccing.py         # очистка, нормализация, автоопределение колонок
│   ├── relations_entity.py         # извлечение сущностей, действий и отношений
│   ├── ner_proceccing.py           # построение графа знаний и совместимый фасад
│   ├── candidate_builder.py        # формирование кандидатов комплексных проблем
│   ├── complex_problem_score.py    # расчет индекса комплексности
│   ├── llm_service.py              # LLM/heuristic-интерпретация карточек
│   └── ai_agent.py                 # финальный аналитический агент
│
├── city_assistant_ui/
│   ├── app.py                      # Streamlit-интерфейс
│   ├── artifacts/
│   │   └── default/                # сюда сохраняются результаты пайплайна
│   └── city_assistant/
│       ├── config.py               # настройки UI
│       ├── data_repository.py      # загрузка артефактов
│       ├── retrieval.py            # поиск релевантных проблем
│       ├── chat_service.py         # логика ответов помощника
│       ├── ui_components.py        # карточки проблем
│       └── report_renderer.py      # рендер отчетов
│
├── requirements.txt
└── README.md
```

> Названия `clean_proceccing.py` и `ner_proceccing.py` сохранены намеренно, чтобы не ломать существующую структуру проекта.

---

## Основной результат пайплайна

Главный артефакт проекта:

```text
city_assistant_ui/artifacts/default/json/problem_candidates.jsonl
```

Одна строка JSONL = одна карточка кандидата комплексной городской проблемы.

Пример структуры:

```json
{
  "candidate_id": "kp_001",
  "title": "Нарушение теплоснабжения в жилом секторе",
  "problem_type": "жилищно-коммунальное",
  "complexity_score": 0.82,
  "score_factors": {
    "frequency": 120,
    "unique_entities": 34,
    "unique_actions": 12,
    "relations_count": 98,
    "subgraph_density": 0.18
  },
  "evidence_appeals": [
    {
      "doc_index": 15,
      "text": "...",
      "date": "...",
      "address": "..."
    }
  ],
  "entities": ["дом", "квартира", "управляющая компания"],
  "actions": ["отсутствовать", "ремонтировать", "обращаться"],
  "actors": ["жители", "управляющая компания"],
  "relations": [
    {
      "subject": "жители",
      "action": "обращаться",
      "object": "управляющая компания"
    }
  ],
  "llm_summary": {
    "short_title": "...",
    "problem_essence": "...",
    "why_complex": "...",
    "management_actions": []
  }
}
```

Именно этот файл используется интерфейсом ИИ-помощника.

---

## Установка

Рекомендуемая версия Python: **3.10+**.

Создай виртуальное окружение:

```bash
python -m venv .venv
```

Активируй его:

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Установи зависимости:

```bash
pip install -r requirements.txt
```

Если используется Excel-файл, нужен `openpyxl`. Он уже указан в `requirements.txt`.

---

## Быстрый запуск на примере `data_all.xlsx`

Положи файл данных в корень проекта:

```text
data_all.xlsx
```

Для быстрой проверки лучше сначала запустить обработку на части данных:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --max-rows 5000 \
  --min-appeals 3 \
  --min-relations 5
```

Полный запуск:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --min-appeals 5 \
  --min-relations 8
```

После завершения в консоли появится количество найденных кандидатов комплексных проблем и путь к `artifact_index.json`.

---

## Запуск интерфейса ИИ-помощника

После генерации артефактов запусти Streamlit:

```bash
streamlit run city_assistant_ui/app.py
```

Интерфейс читает результаты из:

```text
city_assistant_ui/artifacts/default/
```

В интерфейсе можно:

- смотреть топ комплексных проблем;
- фильтровать проблемы по индексу комплексности;
- раскрывать карточки проблем;
- задавать вопросы городскому ИИ-помощнику;
- получать объяснение, почему проблема считается комплексной.

Примеры вопросов:

```text
Какие проблемы самые комплексные?
```

```text
Почему проблема с отоплением считается комплексной?
```

```text
Какие обращения подтверждают эту проблему?
```

```text
Какие управленческие действия можно предложить?
```

---

## Формат входных данных

Пайплайн поддерживает `.xlsx`, `.xls` и `.csv`.

Желательные колонки:

| Поле | Назначение |
|---|---|
| `Текст` | основной текст обращения |
| `Дата создания` | дата обращения |
| `Направление` / `Категория` / `Область обращения` | тематика обращения |
| `Адрес` / `Улица` | территориальный признак, если есть |
| `Источник` | канал поступления, если есть |

Для файла `data_all.xlsx` используются:

| Логическое поле | Колонка в файле |
|---|---|
| текст обращения | `Текст` |
| дата | `Дата создания` |
| категория | `Направление` |
| адрес | извлекается из текста эвристически, если отдельной колонки нет |

Если названия колонок отличаются, их можно указать вручную:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --text-column "Текст" \
  --date-column "Дата создания" \
  --category-column "Направление"
```

Если есть адресная колонка:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --text-column "Текст" \
  --date-column "Дата создания" \
  --address-column "Адрес" \
  --category-column "Направление"
```

---

## Параметры пайплайна

```bash
python process/main.py --help
```

Основные параметры:

| Параметр | Значение |
|---|---|
| `--input` | путь к исходному `.xlsx`, `.xls` или `.csv` |
| `--output-dir` | папка для артефактов |
| `--text-column` | колонка с текстом обращения |
| `--date-column` | колонка с датой |
| `--address-column` | колонка с адресом |
| `--category-column` | колонка с категорией |
| `--max-rows` | ограничение количества строк для тестового запуска |
| `--min-appeals` | минимальное число обращений для кандидата проблемы |
| `--min-relations` | минимальное число отношений для кандидата проблемы |
| `--max-candidates` | максимальное количество кандидатов |
| `--run-llm` | включить LLM-суммаризацию через внешний backend |

---

## Артефакты после запуска

После обработки создается структура:

```text
city_assistant_ui/artifacts/default/
├── artifact_index.json
├── tables/
│   ├── 00_raw_dataset.csv
│   ├── 01_cleaned_dataset.csv
│   ├── 02_entities.csv
│   ├── 02_entity_statistics.csv
│   ├── 03_relations.csv
│   └── 05_problem_candidates.csv
├── json/
│   ├── 01_preprocessing_report.json
│   ├── 04_graph_density.json
│   ├── 04_graph_summary.json
│   ├── 06_agent_payload.json
│   ├── 06_final_agent_report.json
│   └── problem_candidates.jsonl
└── graphs/
    └── ...
```

Назначение основных файлов:

| Файл | Для чего нужен |
|---|---|
| `01_cleaned_dataset.csv` | очищенные обращения |
| `02_entities.csv` | извлеченные сущности и признаки |
| `03_relations.csv` | отношения субъект — действие — объект |
| `05_problem_candidates.csv` | табличный список кандидатов проблем |
| `problem_candidates.jsonl` | полные карточки кандидатов для UI и LLM |
| `artifact_index.json` | индекс всех созданных файлов |

---

## Индекс комплексности

`Complexity_score` рассчитывается на основе нескольких групп признаков:

- частота обращений;
- количество уникальных сущностей;
- количество уникальных действий;
- количество отношений;
- плотность локального подграфа;
- штраф за слишком простые случаи.

Важно: высокая частота сама по себе не считается доказательством комплексности. Проблема получает высокий индекс, если она подтверждается не только количеством сообщений, но и структурой связей между обращениями, объектами, действиями, акторами и территориями.

---

## LLM-режим

По умолчанию проект работает без внешней LLM в `heuristic`-режиме. Это значит, что карточки и ответы помощника формируются на основе уже рассчитанных метрик и правил.

Для подключения локальной LLM через Ollama:

```bash
export LLM_BACKEND=ollama
export OLLAMA_MODEL=mistral
```

Затем запусти пайплайн с флагом `--run-llm`:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --run-llm
```

По умолчанию используется адрес Ollama:

```text
http://localhost:11434/api/chat
```

Его можно изменить:

```bash
export OLLAMA_URL=http://localhost:11434/api/chat
```

LLM используется только для интерпретации уже найденных кандидатов проблем. Она не должна:

- пересчитывать `Complexity_score`;
- менять метрики;
- добавлять проблемы, которых нет во входных данных;
- делать выводы без подтверждающих обращений.

---

## Настройки интерфейса

Интерфейс можно настраивать через переменные окружения:

| Переменная | Значение по умолчанию | Назначение |
|---|---|---|
| `CITY_ASSISTANT_SCENARIO` | `default` | сценарий/папка артефактов |
| `CITY_ASSISTANT_CANDIDATES_JSONL` | `json/problem_candidates.jsonl` | путь к JSONL относительно сценария |
| `CITY_ASSISTANT_PROBLEMS_CSV` | `tables/05_problem_candidates.csv` | путь к CSV относительно сценария |
| `CITY_ASSISTANT_CHAT_MODE` | `heuristic` | режим ответов помощника |
| `CITY_ASSISTANT_TOP_K` | `10` | число кандидатов для контекста ответа |

Пример:

```bash
export CITY_ASSISTANT_SCENARIO=default
export CITY_ASSISTANT_CHAT_MODE=heuristic
streamlit run city_assistant_ui/app.py
```

---

## Как обновить результаты

Если изменились данные или параметры фильтрации, достаточно заново запустить пайплайн:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default
```

После этого перезапусти Streamlit или обнови страницу интерфейса.

---

## Типовой рабочий сценарий

1. Положить исходный файл данных в корень проекта.
2. Запустить пайплайн на части данных:

```bash
python process/main.py --input data_all.xlsx --output-dir city_assistant_ui/artifacts/default --max-rows 5000
```

3. Проверить, что появились кандидаты проблем:

```text
city_assistant_ui/artifacts/default/json/problem_candidates.jsonl
```

4. Запустить полный расчет:

```bash
python process/main.py --input data_all.xlsx --output-dir city_assistant_ui/artifacts/default
```

5. Открыть интерфейс:

```bash
streamlit run city_assistant_ui/app.py
```

6. Проверить топ проблем и карточки в UI.

---

## Возможные проблемы и решения

### Не найден файл данных

Проверь путь в `--input`.

```bash
python process/main.py --input ./data_all.xlsx
```

### Не определилась колонка с текстом

Передай ее явно:

```bash
python process/main.py --input data_all.xlsx --text-column "Текст"
```

### Нет кандидатов проблем

Попробуй ослабить пороги:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --min-appeals 2 \
  --min-relations 3
```

### Streamlit не видит результаты

Убедись, что существует файл:

```text
city_assistant_ui/artifacts/default/json/problem_candidates.jsonl
```

И что UI запускается из корня проекта:

```bash
streamlit run city_assistant_ui/app.py
```

### Ollama не отвечает

Проверь, что Ollama запущена и модель доступна:

```bash
ollama list
ollama run mistral
```

Если LLM не нужна, не используй `--run-llm`: проект будет работать в heuristic-режиме.

---
