from __future__ import annotations
import html, re
from datetime import datetime, timedelta
from typing import Any, Optional
import pandas as pd
try:
    import pymorphy3
except Exception:
    pymorphy3=None

STOP=set('и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было вот от меня еще нет о из ему теперь когда даже ну ли если уже или ни быть был до для мы про это этот эта эти их при над под без'.split())|{"прошу","мера","обращение","вопрос","администрация","город","район","ответ","здравствуйте","добрый","день"}
TEXT_COLS=["Текст","text","Текст обращения","Сообщение","Описание"]
DATE_COLS=["Дата создания","Дата","created_at","date"]
ADDR_COLS=["Улица","Адрес","address","Место","Локация"]
CAT_COLS=["Направление","Категория","Область обращения","Тема","category"]

def first_col(df, candidates):
    low={str(c).lower():c for c in df.columns}
    for c in candidates:
        if c in df.columns: return c
        if c.lower() in low: return low[c.lower()]
    return None

class TextPreprocessor:
    """Очистка обращений. Поддерживает data_all.xlsx: Направление, Дата создания, Текст."""
    def __init__(self, language="russian", use_lemmatization=True):
        self.language=language; self.use_lemmatization=use_lemmatization
        self.morph=pymorphy3.MorphAnalyzer() if pymorphy3 and use_lemmatization else None
    def infer_columns(self, df, text_column=None, date_column=None, address_column=None, category_column=None):
        text=text_column if text_column in df.columns else first_col(df,TEXT_COLS)
        if not text: raise ValueError(f"Не найдена колонка текста. Колонки: {list(df.columns)}")
        return {"text":text,"date":date_column if date_column in df.columns else first_col(df,DATE_COLS),"address":address_column if address_column in df.columns else first_col(df,ADDR_COLS),"category":category_column if category_column in df.columns else first_col(df,CAT_COLS)}
    @staticmethod
    def parse_date(v:Any)->Optional[str]:
        if pd.isna(v): return None
        if isinstance(v,(int,float)) and 20000<float(v)<80000:
            return (datetime(1899,12,30)+timedelta(days=float(v))).date().isoformat()
        d=pd.to_datetime(v,errors="coerce",dayfirst=True)
        return None if pd.isna(d) else d.date().isoformat()
    @staticmethod
    def clean_text(x:Any)->str:
        if pd.isna(x): return ""
        s=html.unescape(str(x)).replace("ё","е").replace("Ё","Е")
        s=re.sub(r"<br\s*/?>"," ",s,flags=re.I); s=re.sub(r"<[^>]+>"," ",s)
        s=re.sub(r"https?://\S+|www\.\S+|@[\w_]+|#[\wа-яА-ЯёЁ_-]+"," ",s)
        s=re.sub(r"[^0-9a-zA-Zа-яА-Я\-№/.,;:!?\s]"," ",s)
        return re.sub(r"\s+"," ",s).strip()
    @staticmethod
    def tokenize(s:str): return re.findall(r"[а-яА-Яa-zA-Z][а-яА-Яa-zA-Z\-]{2,}|\d+[а-яА-Яa-zA-Z]?", str(s).lower())
    def lemmatize_tokens(self,tokens):
        out=[]
        for t in tokens:
            if t in STOP or len(t)<3: continue
            if self.morph:
                try: t=self.morph.parse(t)[0].normal_form
                except Exception: pass
            if t not in STOP: out.append(t)
        return out
    @staticmethod
    def extract_address_from_text(text:str)->Optional[str]:
        pats=[r"(?:ул\.?|улица)\s+[А-Яа-яA-Za-z0-9\-\s]{2,40}?\s+(?:д\.?|дом)?\s*\d+[а-яА-Яa-zA-Z0-9/\-]*", r"[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁа-яё]+){0,2}\s+\d+[а-яА-Яa-zA-Z0-9/\-]*(?:\s+корпус\s+\d+)?"]
        for p in pats:
            m=re.search(p,text or "",flags=re.I)
            if m: return re.sub(r"\s+"," ",m.group(0)).strip(" ,.;")[:120]
        return None
    @staticmethod
    def emotion_score(text:str)->float:
        q=(text or "").lower(); markers=["ужас","кошмар","невозможно","позор","бездейств","опасн","надоело"]
        return round(min((sum(m in q for m in markers)+min(q.count('!'),3)*.5)/5,1),3)
    @staticmethod
    def urgency_flag(text:str)->bool:
        q=(text or "").lower(); return any(x in q for x in ["срочно","опасно","авария","угроза","немедленно","пожар"])
    def preprocess_dataframe(self, df, text_column=None, date_column=None, address_column=None, category_column=None, max_rows=None):
        m=self.infer_columns(df,text_column,date_column,address_column,category_column); out=df.head(max_rows).copy() if max_rows else df.copy()
        out["appeal_id"]=[f"appeal_{i:06d}" for i in range(len(out))]
        out["raw_text"]=out[m["text"]].fillna("").astype(str); out["clean_text"]=out["raw_text"].map(self.clean_text)
        out["text_tokens"]=out["clean_text"].map(self.tokenize); out["text_lemmatized_tokens"]=out["text_tokens"].map(self.lemmatize_tokens); out["text_lem"]=out["text_lemmatized_tokens"].map(lambda x:" ".join(x))
        out["text_length"]=out["clean_text"].str.len(); out["emotion_score"]=out["clean_text"].map(self.emotion_score); out["urgency_flag"]=out["clean_text"].map(self.urgency_flag)
        out["date_norm"]=out[m["date"]].map(self.parse_date) if m["date"] else None
        out["address_norm"]=out[m["address"]].fillna("").astype(str).str.strip() if m["address"] else out["clean_text"].map(self.extract_address_from_text)
        out["category_norm"]=out[m["category"]].fillna("другое").astype(str).str.strip() if m["category"] else "другое"
        out["source_text_column"]=m["text"]; out["source_date_column"]=m["date"]; out["source_address_column"]=m["address"]; out["source_category_column"]=m["category"]
        return out
    def get_preprocessing_report(self, df):
        return {"rows":int(len(df)),"non_empty_texts":int(df["clean_text"].str.len().gt(0).sum()) if len(df) else 0,"date_coverage":float(df["date_norm"].notna().mean()) if len(df) else 0,"address_coverage":float(df["address_norm"].fillna('').astype(str).str.len().gt(0).mean()) if len(df) else 0,"category_top":df["category_norm"].value_counts().head(20).to_dict() if len(df) else {}}
