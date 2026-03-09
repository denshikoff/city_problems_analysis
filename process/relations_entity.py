import pandas as pd
import string
import spacy
from typing import List, Dict, Optional, Set

class UrbanProblemsGraphExtractor:
    """Класс для извлечения сущностей и связей для построения графа городских проблем"""
    
    def __init__(self, spacy_model: str = "ru_core_news_sm"):
        """
        Инициализация экстрактора графа
        
        Args:
            spacy_model: Название модели SpaCy для русского языка
        """
        self.nlp = spacy.load(spacy_model)
        
        # POS-теги, которые считаем "мусором"
        self.bad_pos = {"ADP", "CCONJ", "SCONJ", "PRON", "PART", 
                       "DET", "INTJ", "SYM", "PUNCT", "X"}
        
        # Словарь для переименования сущностей
        self.entity_renames = {
            "id|": "житель",
            "id_": "житель",
            "id-": "житель",
            "номер": "житель",
            "аноним": "житель"
        }
    
    def _is_valid_entity(self, text: str) -> bool:
        """
        Проверка, является ли текст валидной сущностью
        
        Args:
            text: Текст для проверки
            
        Returns:
            True если сущность валидна, False иначе
        """
        text = text.strip()
        
        # Проверка на пустоту или только пунктуацию
        if not text or all(char in string.punctuation for char in text):
            return False
        
        # Анализ с помощью SpaCy
        doc = self.nlp(text)
        for token in doc:
            if token.pos_ in self.bad_pos:
                return False
        
        return True
    
    def _normalize_entity(self, entity: str) -> str:
        """
        Нормализация названия сущности
        
        Args:
            entity: Исходное название сущности
            
        Returns:
            Нормализованное название
        """
        entity = entity.strip().lower()
        
        # Переименование ID-подобных сущностей
        for pattern, replacement in self.entity_renames.items():
            if pattern in entity:
                return replacement
        
        # Удаление лишних пробелов и возврат с правильным регистром
        return entity.strip().capitalize()
    
    def _extract_relations_from_sentence(self, sent, doc_idx: int) -> List[Dict]:
        """
        Извлечение отношений из одного предложения
        
        Args:
            sent: Объект предложения SpaCy
            doc_idx: Индекс документа в исходном DataFrame
            
        Returns:
            Список отношений из предложения
        """
        relations = []
        subj = None
        obj = None
        verb = None
        
        for token in sent:
            # Поиск глагола (действия/проблемы)
            if token.pos_ == "VERB":
                verb = token.lemma_
            
            # Поиск подлежащего (субъекта)
            if token.dep_ in ("nsubj", "nsubj:pass"):
                subj = token.text
            
            # Поиск дополнения (объекта)
            if token.dep_ in ("obj", "dobj", "obl", "iobj"):
                obj = token.text
        
        # Если найдены все компоненты
        if subj and verb and obj:
            # Проверка валидности сущностей
            if self._is_valid_entity(subj) and self._is_valid_entity(obj):
                # Нормализация сущностей
                subj = self._normalize_entity(subj)
                obj = self._normalize_entity(obj)
                
                relations.append({
                    'Объект': obj,
                    'Связь': verb,
                    'Субъект': subj,
                    'doc_index': doc_idx,
                    'sentence_text': sent.text
                })
        
        return relations
    

    def extract_entities(self, df_source: pd.DataFrame, text_column: str = "Текст") -> pd.DataFrame:
        """
        Извлечение NER-сущностей по каждому документу.
        Сохраняет исходный текст сущности, метку и нормализованную форму.
        """
        if text_column not in df_source.columns:
            raise ValueError(f"Колонка '{text_column}' не найдена в DataFrame")

        entities = []
        for idx, text in enumerate(df_source[text_column]):
            if not isinstance(text, str):
                text = "" if pd.isna(text) else str(text)

            doc = self.nlp(text)
            for ent in doc.ents:
                norm = self._normalize_entity(ent.text)
                entities.append({
                    "doc_index": idx,
                    "entity": ent.text,
                    "entity_normalized": norm,
                    "label": ent.label_,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                    "context": text[max(0, ent.start_char - 80): min(len(text), ent.end_char + 80)].strip()
                })

        if not entities:
            return pd.DataFrame(columns=[
                "doc_index", "entity", "entity_normalized", "label",
                "start_char", "end_char", "context"
            ])

        return pd.DataFrame(entities).drop_duplicates().reset_index(drop=True)

    def get_entity_statistics(self, entities_df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
        """Агрегированная статистика по сущностям NER."""
        if entities_df is None or entities_df.empty:
            return pd.DataFrame(columns=["entity_normalized", "label", "count", "documents_count"])

        stats = (
            entities_df.groupby(["entity_normalized", "label"], dropna=False)
            .agg(
                count=("entity", "size"),
                documents_count=("doc_index", pd.Series.nunique),
                variants=("entity", lambda s: sorted(set(map(str, s)))[:10])
            )
            .reset_index()
            .sort_values(["count", "documents_count"], ascending=False)
            .head(top_n)
        )
        return stats

    def extract_relations(self, df_source: pd.DataFrame, text_column: str = "text_lem") -> pd.DataFrame:
        """
        Основной метод извлечения отношений из DataFrame
        
        Args:
            df_source: Исходный DataFrame с текстами
            text_column: Название колонки с текстом (лемматизированным)
            
        Returns:
            DataFrame с колонками: Объект, Связь, Субъект
        """
        relations_data = []
        
        # Проверка наличия необходимой колонки
        if text_column not in df_source.columns:
            raise ValueError(f"Колонка '{text_column}' не найдена в DataFrame")
        
        for idx, text_list in enumerate(df_source[text_column]):
            # Объединение лемм в текст
            if isinstance(text_list, list):
                text = " ".join(text_list)
            else:
                text = str(text_list)
            
            # Анализ текста
            doc = self.nlp(text)
            
            # Извлечение отношений из каждого предложения
            for sent in doc.sents:
                relations = self._extract_relations_from_sentence(sent, idx)
                relations_data.extend(relations)
        
        # Создание DataFrame и удаление дубликатов
        if relations_data:
            result_df = pd.DataFrame(relations_data)
            result_df = result_df[['Объект', 'Связь', 'Субъект']]  # Выбор нужных колонок
            result_df = result_df.drop_duplicates().reset_index(drop=True)
        else:
            result_df = pd.DataFrame(columns=['Объект', 'Связь', 'Субъект'])
        
        return result_df
    
    def extract_with_context(self, df_source: pd.DataFrame, text_column: str = "text_lem") -> pd.DataFrame:
        """
        Извлечение отношений с дополнительным контекстом
        
        Args:
            df_source: Исходный DataFrame с текстами
            text_column: Название колонки с текстом
            
        Returns:
            DataFrame с полной информацией об отношениях
        """
        relations_data = []
        
        if text_column not in df_source.columns:
            raise ValueError(f"Колонка '{text_column}' не найдена в DataFrame")
        
        for idx, text_list in enumerate(df_source[text_column]):
            if isinstance(text_list, list):
                text = " ".join(text_list)
            else:
                text = str(text_list)
            
            doc = self.nlp(text)
            
            for sent in doc.sents:
                relations = self._extract_relations_from_sentence(sent, idx)
                relations_data.extend(relations)
        
        if relations_data:
            result_df = pd.DataFrame(relations_data)
            result_df = result_df.drop_duplicates().reset_index(drop=True)
        else:
            result_df = pd.DataFrame(columns=[
                'Объект', 'Связь', 'Субъект', 'doc_index', 'sentence_text'
            ])
        
        return result_df