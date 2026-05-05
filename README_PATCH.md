# Патч переработки реализации ВКР

## Что заменить/добавить

Скопируй `process/` в папку `process/` репозитория, а `city_assistant_ui/` — в `city_assistant_ui/`.

Главный новый артефакт между обработкой, LLM и UI:

```text
city_assistant_ui/artifacts/<scenario>/json/problem_candidates.jsonl
```

Одна строка JSONL = карточка кандидата комплексной проблемы: метрики, score_factors, подтверждающие обращения, сущности, действия, связи, контекст и summary.

## Быстрый запуск на data_all.xlsx

Проверка на части данных:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --max-rows 5000 \
  --min-appeals 3 \
  --min-relations 5
```

Полный файл:

```bash
python process/main.py \
  --input data_all.xlsx \
  --output-dir city_assistant_ui/artifacts/default \
  --min-appeals 5 \
  --min-relations 8
```

Интерфейс:

```bash
streamlit run city_assistant_ui/app.py
```

## Под твой файл

Автоопределяются колонки: `Текст`, `Дата создания`, `Направление`. Адресной колонки в файле нет, поэтому адрес извлекается из текста эвристически.

## LLM

Без модели работает heuristic-режим. Для локальной LLM через Ollama:

```bash
export LLM_BACKEND=ollama
export OLLAMA_MODEL=mistral
python process/main.py --input data_all.xlsx --output-dir city_assistant_ui/artifacts/default --run-llm
```
