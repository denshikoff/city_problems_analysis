from __future__ import annotations
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Tuple
import pandas as pd

def norm(x:Any)->str: return re.sub(r"\s+"," ",str(x or "").lower().replace("ё","е")).strip(" .,:;!?-—")
def uniq(xs:Iterable[str], n:int=99)->List[str]:
    seen=set(); out=[]
    for x in xs:
        x=norm(x)
        if x and x not in seen: seen.add(x); out.append(x)
        if len(out)>=n: break
    return out

class UrbanProblemsGraphExtractor:
    OBJECTS={"дворовая территория":["двор","дворовая территория","придомовая территория"],"снег и наледь":["снег","наледь","гололед","сугроб","лед"],"дорога":["дорога","проезжая часть","асфальт","ям","колея"],"тротуар":["тротуар","пешеходная дорожка"],"освещение":["фонарь","освещение","свет","лампа"],"мусор":["мусор","тко","контейнер","помойка","свалка","отход"],"отопление":["отопление","батарея","тепло","теплоснабжение"],"водоснабжение":["вода","водоснабжение","труба","протечка","канализация","затопление"],"подъезд":["подъезд","лестница"],"крыша":["крыша","кровля"],"лифт":["лифт"],"детская площадка":["детская площадка","площадка","качели","горка"],"парк/сквер":["парк","сквер","газон"],"общественный транспорт":["автобус","трамвай","троллейбус","маршрут","остановка","транспорт"],"здание/дом":["дом","мкд","здание"]}
    ACTORS={"жители":["житель","жители","люди","горожане","мы","нас"],"управляющая компания":["управляющая компания","ук","жэк","жкх","тсж"],"администрация":["администрация","мэрия","управа"],"подрядчик":["подрядчик","служба","коммунальщики","дорожники"],"ресурсоснабжающая организация":["водоканал","теплосеть","энергетики"]}
    ACTIONS={"не убирает":["не убира","не чист","не вывоз","завален","засыпан"],"не работает":["не работает","не горит","сломал","поломан"],"не устраняет":["не устраня","бездейств","не реагир","не принимает меры"],"повреждено":["разбит","разруш","поврежд","яма","трещин","провал"],"отсутствует":["нет","отсутств","не хватает"],"загрязнено":["гряз","загряз","свалк","мусор"],"опасно":["опасн","угроза","травм","аварийн"],"затоплено":["течет","затоп","луж","вода стоит","протеч"],"задержано":["задерж","срок","долго","месяц","год"]}
    ANCHORS={"нарушение содержания территории":["не убира","гряз","снег","наледь","мусор","сугроб"],"техническая неисправность":["не работает","сломал","поломан","не горит"],"аварийное состояние":["авария","аварийн","опасн","угроза","разруш"],"затопление/протечка":["затоп","течет","протеч","луж","вода"],"отсутствие услуги":["нет отопления","нет воды","отсутств","не хватает"],"бездействие исполнителя":["бездейств","не реагир","не устраня","жалоб","обращал"]}
    THEME={"дворовая территория":"благоустройство","снег и наледь":"благоустройство","дорога":"инфраструктура","тротуар":"инфраструктура","освещение":"безопасность","мусор":"жилищно-коммунальное","отопление":"жилищно-коммунальное","водоснабжение":"жилищно-коммунальное","подъезд":"жилищно-коммунальное","крыша":"жилищно-коммунальное","лифт":"жилищно-коммунальное","детская площадка":"благоустройство","парк/сквер":"благоустройство","общественный транспорт":"транспорт","здание/дом":"жилищно-коммунальное"}
    def __init__(self):
        self.rx={name:self._compile(d) for name,d in [("objects",self.OBJECTS),("actors",self.ACTORS),("actions",self.ACTIONS),("anchors",self.ANCHORS)]}
    @staticmethod
    def _compile(d:Dict[str,Sequence[str]]): return [(k,re.compile("(?:"+"|".join(re.escape(v).replace("\\ ",r"\s+") for v in vs)+")",re.I)) for k,vs in d.items()]
    def _find(self,text,kind): return uniq(k for k,rx in self.rx[kind] if rx.search(text or ""))
    def detect_objects(self,text): return self._find(text,"objects")
    def detect_actors(self,text): return self._find(text,"actors") or ["жители"]
    def detect_actions(self,text): return self._find(text,"actions") or ["сообщает о проблеме"]
    def detect_anchors(self,text): return self._find(text,"anchors") or ["проблемный сигнал"]
    def extract_entities(self, df, text_column="clean_text"):
        rows=[]
        for idx,r in df.iterrows():
            text=str(r.get(text_column) or r.get("clean_text") or r.get("raw_text") or ""); aid=r.get("appeal_id",f"appeal_{idx:06d}"); cat=norm(r.get("category_norm") or "другое"); addr=norm(r.get("address_norm") or "")
            groups=[("object",self.detect_objects(text)),("actor",self.detect_actors(text)),("action",self.detect_actions(text)),("problem_anchor",self.detect_anchors(text)),("theme",[cat] if cat else []),("territory",[addr] if addr else [])]
            for typ,vals in groups:
                for v in vals: rows.append({"doc_index":int(idx),"appeal_id":aid,"entity":v,"normalized":norm(v),"entity_type":typ,"category":cat,"address":addr,"date":r.get("date_norm"),"context":text[:500]})
        return pd.DataFrame(rows)
    def extract_with_context(self, df, text_column="clean_text"):
        rows=[]
        for idx,r in df.iterrows():
            text=str(r.get(text_column) or r.get("clean_text") or r.get("raw_text") or ""); aid=r.get("appeal_id",f"appeal_{idx:06d}"); cat=norm(r.get("category_norm") or "другое"); addr=norm(r.get("address_norm") or "")
            objects=self.detect_objects(text) or ([cat] if cat else []); actors=self.detect_actors(text); actions=self.detect_actions(text); anchors=self.detect_anchors(text)
            for obj in objects:
                theme=self.THEME.get(obj,cat or "другое")
                for actor in actors[:3]:
                    for action in actions[:4]:
                        for anchor in anchors[:3]: rows.append({"doc_index":int(idx),"appeal_id":aid,"Субъект":actor,"Связь":action,"Объект":obj,"Проблемный_признак":anchor,"Тема":theme,"Категория_источника":cat,"Адрес":addr,"Дата":r.get("date_norm"),"Контекст":text[:700],"raw_text":str(r.get("raw_text") or text)[:1200],"emotion_score":float(r.get("emotion_score") or 0),"urgency_flag":bool(r.get("urgency_flag") or False)})
        return pd.DataFrame(rows)
    @staticmethod
    def get_entity_statistics(entities_df):
        if entities_df is None or entities_df.empty: return pd.DataFrame(columns=["entity_type","normalized","count"])
        return entities_df.groupby(["entity_type","normalized"],dropna=False).size().reset_index(name="count").sort_values(["entity_type","count"],ascending=[True,False])
