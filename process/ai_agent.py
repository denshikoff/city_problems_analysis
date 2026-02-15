import json
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig



MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"


class LocalLLMAgent:
    def __init__(self):
        print("⏳ Загружаю локальную модель...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto"
        )
        print("✅ Модель загружена")

    def _extract_json(self, text: str) -> dict:
      # убираем code fences, если модель их вставила
      text = text.replace("```json", "").replace("```", "")
  
      last_obj = None
      stack = 0
      start = None
  
      for i, ch in enumerate(text):
          if ch == "{":
              if stack == 0:
                  start = i
              stack += 1
          elif ch == "}":
              if stack > 0:
                  stack -= 1
                  if stack == 0 and start is not None:
                      candidate = text[start:i+1]
                      # пробуем распарсить — если это JSON, запоминаем как последний валидный
                      try:
                          last_obj = json.loads(candidate)
                      except Exception:
                          pass
                      start = None

      if last_obj is None:
          raise ValueError("Не удалось найти валидный JSON-объект в ответе модели")
  
      return last_obj
    


    def run(self, agent_payload: dict) -> dict:
        payload_json = json.dumps(agent_payload, ensure_ascii=False, indent=2)
        prompt = """
            ТЫ АНАЛИТИЧЕСКИЙ АГЕНТ.

        На входе — список городских проблем.
        Для КАЖДОЙ проблемы уже рассчитан показатель Complexity_score (0..1)
        на основе структурных и графовых метрик.
        
        ТВОЯ ЗАДАЧА:
        1. Проанализировать распределение проблем по уровню комплексности
        2. Выделить:
           - системные проблемы (Complexity_score ≥ 0.7)
           - средние по сложности (0.4–0.7)
           - локальные проблемы (< 0.4)
        3. Объяснить, ПОЧЕМУ наиболее комплексные проблемы являются системными
           (через субъекты, действия, плотность связей)
        4. Выявить общие паттерны:
           - межведомственные проблемы
           - инфраструктурные узлы
           - повторяющиеся причины
        5. Сделать аналитические выводы, пригодные для управленческого отчёта.
        
        ОГРАНИЧЕНИЯ:
        - НЕ пересчитывай Complexity_score
        - НЕ меняй входные данные
        - НЕ добавляй новые проблемы
        - Используй ТОЛЬКО предоставленные данные
        
        ВЕРНИ СТРОГО JSON БЕЗ ЛЮБОГО ТЕКСТА.
        
        ФОРМАТ ОТВЕТА (НЕ МЕНЯТЬ КЛЮЧИ):
        
        {
          "summary": {
            "total_problems": number,
            "systemic_problems_count": number,
            "local_problems_count": number
          },
          "systemic_problems": [
            {
              "problem": string,
              "complexity_score": number,
              "reason": string
            }
          ],
          "key_patterns": [string],
          "management_insights": [string],
          "confidence": number
        }
        
        ДАННЫЕ:
        """ + payload_json


        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                temperature=0.1,
                do_sample=True
            )

        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        try:
            return self._extract_json(text)
        except Exception as e:
            return {
                "error": "Не удалось распарсить JSON",
                "raw_output": text,
                "exception": str(e)
            }


# Singleton агент (чтобы модель грузилась 1 раз)
_agent = None


def run_agent(agent_payload: dict) -> dict:
    global _agent
    if _agent is None:
        _agent = LocalLLMAgent()
    return _agent.run(agent_payload)
