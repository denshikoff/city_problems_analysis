import re
import pandas as pd
from typing import List, Optional, Dict, Any
import pymorphy3
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import nltk
from datetime import datetime

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

DEFAULT_CUSTOM_STOPWORDS = {
    # служебные
    "это", "там", "здесь", "который", "которая", "которые",
    "быть", "есть", "являться",
    "такой", "такая", "такие",
    "очень", "просто", "вообще",

    # обращения / формальности
    "прошу", "просить", "обращение", "обращаться",
    "сообщать", "сообщение",
    "заявка", "жалоба",

    # временные / абстрактные
    "год", "месяц", "день", "время",
    "сегодня", "вчера", "сейчас",

    # люди (слишком общие)
    "человек", "люди", "житель", "жители"
}


class TextPreprocessor:
    """
    Класс для предобработки текстов обращений граждан.
    Возвращает датафрейм с новыми атрибутами для дальнейшего анализа.
    """
    
    def __init__(self, 
                 language: str = 'russian',
                 use_lemmatization: bool = True,
                 custom_stopwords: Optional[List[str]] = DEFAULT_CUSTOM_STOPWORDS):
        """
        Инициализация препроцессора
        
        Args:
            language: Язык текстов
            use_lemmatization: Использовать лемматизацию
            custom_stopwords: Дополнительные стоп-слова
        """
        self.language = language
        self.use_lemmatization = use_lemmatization
        
        # Базовые стоп-слова
        self.stopwords = set(stopwords.words(language))
        
        # Добавляем пользовательские стоп-слова
        if custom_stopwords:
            self.stopwords.update(custom_stopwords)
        
        # Инициализация лемматизатора
        if use_lemmatization and language == 'russian':
            self.morph = pymorphy3.MorphAnalyzer()
        else:
            self.morph = None
            
        # Дополнительные символы для удаления
        self.punctuation = set(string.punctuation)
        self.punctuation.update(['«', '»', '—', '–', '…', '•', '●', '✅', '❌', '⚠️'])
    
    def clean_text(self, text: str) -> str:
        """
        Базовая очистка текста
        """
        if not isinstance(text, str):
            return ""
        
        # Приведение к нижнему регистру
        text = text.lower().strip()
        
        # Удаление URL
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Удаление email
        text = re.sub(r'\S+@\S+', '', text)
        
        # Удаление телефонов
        text = re.sub(r'[\+\d\s\-\(\)]{7,}', '', text)
        
        # Удаление дат в формате дд.мм.гггг
        text = re.sub(r'\d{1,2}\.\d{1,2}\.\d{2,4}', '', text)
        
        # Удаление эмодзи и специальных символов
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U00002700-\U000027BF'
            r'\U0001F680-\U0001F6FF\U0001F1E6-\U0001F1FF\U0001F900-\U0001F9FF]+',
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Токенизация текста
        """
        return word_tokenize(text, language=self.language)
    
    def lemmatize_token(self, token: str) -> str:
        """
        Лемматизация одного токена
        """
        if self.morph and token:
            parsed = self.morph.parse(token)[0]
            return parsed.normal_form
        return token
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """
        Лемматизация списка токенов
        """
        return [self.lemmatize_token(token) for token in tokens]
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Удаление стоп-слов и пунктуации
        """
        filtered_tokens = []
        for token in tokens:
            # Пропускаем пустые токены
            if not token:
                continue
            
            # Пропускаем стоп-слова
            if token in self.stopwords:
                continue
            
            # Пропускаем пунктуацию
            if all(char in self.punctuation for char in token):
                continue
            
            # Пропускаем слишком короткие токены
            if len(token) <= 1:
                continue
            
            filtered_tokens.append(token)
        
        return filtered_tokens
    
    def extract_text_features(self, text: Any) -> Dict[str, Any]:
        """
        Извлечение базовых фич из текста.
        Устойчиво обрабатывает пропуски и нестроковые значения.
        """
        # Защита от NaN / float / других типов
        if not isinstance(text, str):
            original_text = "" if text is None or pd.isna(text) else str(text)
        else:
            original_text = text

        cleaned_text = self.clean_text(original_text)
        tokens = self.tokenize_text(cleaned_text)
        cleaned_tokens = self.remove_stopwords(tokens)
        
        if self.use_lemmatization:
            lemmatized_tokens = self.lemmatize_tokens(cleaned_tokens)
        else:
            lemmatized_tokens = cleaned_tokens
        
        return {
            'length': len(original_text),
            'cleaned_length': len(cleaned_text),
            'token_count': len(tokens),
            'cleaned_token_count': len(cleaned_tokens),
            'word_count': len(cleaned_text.split()),
            'avg_word_length': sum(len(word) for word in cleaned_text.split()) / max(len(cleaned_text.split()), 1),
            'has_urgency_keywords': self._check_urgency_keywords(text),
            'has_emotional_words': self._check_emotional_words(text),
            'cleaned_text': cleaned_text,
            'tokens': tokens,
            'cleaned_tokens': cleaned_tokens,
            'lemmatized_tokens': lemmatized_tokens
        }
    
    def _check_urgency_keywords(self, text: str) -> bool:
        """
        Проверка наличия ключевых слов срочности
        """
        if not isinstance(text, str):
            return False
        urgency_keywords = [
            'срочно', 'немедленно', 'опасно', 'угроза', 'авария', 
            'чрезвычайная', 'экстрен', 'неотлож', 'катастроф',
            'разруш', 'пожар', 'затоп', 'обруш', 'травм'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in urgency_keywords)
    
    def _check_emotional_words(self, text: str) -> bool:
        """
        Проверка наличия эмоционально окрашенных слов
        """
        if not isinstance(text, str):
            return False
        emotional_keywords = [
            'ужас', 'кошмар', 'безобразие', 'невозможно', 'терпеть',
            'возмущ', 'протест', 'требую', 'жалуюсь', 'бездействие',
            'халатность', 'преступление', 'скандал', 'позор'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in emotional_keywords)
    
    def preprocess_dataframe(self, 
                            df: pd.DataFrame, 
                            text_column: str = 'text',
                            date_column: Optional[str] = 'Дата',
                            address_column: Optional[str] = 'Адрес',
                            category_column: Optional[str] = 'Область обращения') -> pd.DataFrame:
        """
        Основной метод предобработки всего датафрейма
        
        Args:
            df: Входной датафрейм
            text_column: Название колонки с текстом
            date_column: Название колонки с датой
            address_column: Название колонки с адресом
            category_column: Название колонки с категорией
            
        Returns:
            Обработанный датафрейм с новыми атрибутами
        """
        # Создаем копию датафрейма
        processed_df = df.copy()
        
        print("Начало предобработки...")
        
        # 1. Предобработка текста
        print("Очистка и анализ текстов...")
        text_features = processed_df[text_column].apply(self.extract_text_features)
       
        # Распаковываем словарь в отдельные колонки
        for key in text_features.iloc[0].keys():
            processed_df[f'text_{key}'] = text_features.apply(lambda x: x[key])
        # 2. Предобработка даты
        if date_column and date_column in processed_df.columns:
            print("Обработка временных меток...")
            processed_df['date_processed'] = pd.to_datetime(
                processed_df[date_column], errors='coerce'
            )
            processed_df['year'] = processed_df['date_processed'].dt.year
            processed_df['month'] = processed_df['date_processed'].dt.month
            processed_df['day'] = processed_df['date_processed'].dt.day
            processed_df['day_of_week'] = processed_df['date_processed'].dt.dayofweek
            processed_df['hour'] = processed_df['date_processed'].dt.hour
            processed_df['is_weekend'] = processed_df['day_of_week'].isin([5, 6])
            
            # Временные метрики
            if len(processed_df) > 1:
                processed_df['days_since_first'] = (
                    processed_df['date_processed'] - processed_df['date_processed'].min()
                ).dt.days
        # 3. Предобработка адреса
        if address_column and address_column in processed_df.columns:
            print("3. Нормализация адресов...")
            processed_df['address_cleaned'] = processed_df[address_column].apply(
                lambda x: str(x).lower().strip() if pd.notna(x) else ''
            )
            
            # Извлечение района из адреса (базовый пример)
            def extract_district(address):
                if not address:
                    return None
                # Здесь можно добавить более сложную логику
                districts = ['центр', 'север', 'юг', 'восток', 'запад', 
                            'левый берег', 'правый берег']
                for district in districts:
                    if district in address:
                        return district
                return None
            
            processed_df['district'] = processed_df['address_cleaned'].apply(extract_district)
        
        # 4. Предобработка категории
        if category_column and category_column in processed_df.columns:
            print("Кодирование категорий...")
            # Создаем бинарные признаки для частых категорий
            category_dummies = pd.get_dummies(
                processed_df[category_column], 
                prefix='category',
                dummy_na=True
            )
            processed_df = pd.concat([processed_df, category_dummies], axis=1)
            
            # Подсчет частоты категорий
            category_counts = processed_df[category_column].value_counts().to_dict()
            processed_df['category_frequency'] = processed_df[category_column].map(
                lambda x: category_counts.get(x, 0)
            )
        
        # 5. Создание комбинированных признаков
        print("Создание комбинированных признаков...")
        processed_df['urgency_score'] = processed_df['text_has_urgency_keywords'].astype(int)
        processed_df['emotion_score'] = processed_df['text_has_emotional_words'].astype(int)
        
        # Общий показатель "важности" обращения
        processed_df['importance_score'] = (
            processed_df['urgency_score'] * 2 + 
            processed_df['emotion_score'] +
            processed_df['text_length'] / processed_df['text_length'].max()
        )
        
        # 6. Информация о токенах для дальнейшего анализа
        print("Подготовка данных для NLP анализа...")
        processed_df['processed_text'] = processed_df['text_lemmatized_tokens'].apply(
            lambda tokens: ' '.join(tokens) if isinstance(tokens, list) else ''
        )
        
        print(f"Предобработка завершена. Добавлено {len(processed_df.columns) - len(df.columns)} новых колонок.")
        
        return processed_df
    
    def get_preprocessing_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Генерация отчета о предобработке
        """
        report = {
            'total_records': len(df),
            'text_columns': [col for col in df.columns if 'text' in col],
            'date_columns': [col for col in df.columns if 'date' in col.lower()],
            'address_columns': [col for col in df.columns if 'addr' in col.lower()],
            'category_columns': [col for col in df.columns if 'category' in col.lower()],
            'new_columns_count': len([col for col in df.columns if col.startswith('text_') or 
                                     col in ['year', 'month', 'day', 'district', 'urgency_score']]),
            'avg_text_length': df['text_length'].mean() if 'text_length' in df.columns else None,
            'avg_token_count': df['text_token_count'].mean() if 'text_token_count' in df.columns else None,
            'urgency_percentage': df['urgency_score'].mean() * 100 if 'urgency_score' in df.columns else None,
            'emotion_percentage': df['emotion_score'].mean() * 100 if 'emotion_score' in df.columns else None
        }
        
        return report

