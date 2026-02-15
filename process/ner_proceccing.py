import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
from collections import Counter
import logging
from datetime import datetime
from complex_problem_score import ComplexProblemScorer

class UrbanKnowledgeGraph:
    """Класс для построения и анализа графа знаний городских проблем"""


    def __init__(self, relations_df: pd.DataFrame, log_level: str = "INFO"):
            """
            Инициализация графа знаний

            Args:
                relations_df: DataFrame с отношениями (Объект, Связь, Субъект)
                log_level: Уровень логирования
            """
            # Настройка логирования
            self.logger = self._setup_logger(log_level)
            self.logger.info("=" * 60)
            self.logger.info(f"Инициализация UrbanKnowledgeGraph")
            self.logger.info(f"Дата и время: {datetime.now()}")

            # Проверка входных данных
            required_columns = {'Объект', 'Связь', 'Субъект'}
            if not all(col in relations_df.columns for col in required_columns):
                missing = required_columns - set(relations_df.columns)
                error_msg = f"Отсутствуют обязательные колонки: {missing}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.relations_df = relations_df.copy()
            self.logger.info(f"Загружено {len(relations_df)} отношений")

            # Инициализация графа
            self.graph = nx.MultiDiGraph()
            self.problems = []
            self.metrics = {}
            self.centrality_df = pd.DataFrame()

            # Словари для классификации проблем
            self.problem_keywords = {
                'инфраструктура': ['дорога', 'тротуар', 'асфальт', 'освещение', 'парковка',
                                   'остановка', 'мост', 'тоннель', 'развязка', 'бордюр'],
                'благоустройство': ['скамейка', 'урна', 'клумба', 'озеленение', 'фонтан',
                                    'парк', 'сквер', 'детская площадка', 'спортивная площадка'],
                'жилищно-коммунальное': ['водоснабжение', 'отопление', 'канализация', 'электричество',
                                         'мусор', 'уборка', 'ремонт', 'крыша', 'подъезд', 'лифт'],
                'транспорт': ['автобус', 'трамвай', 'троллейбус', 'метро', 'такси',
                              'пробка', 'авария', 'движение', 'регулировка', 'знак'],
                'экология': ['воздух', 'вода', 'шум', 'загрязнение', 'свалка', 'выброс',
                             'зелень', 'дерево', 'озеро', 'река'],
                'социальное': ['больница', 'поликлиника', 'школа', 'детский сад', 'библиотека',
                               'дом культуры', 'стадион', 'пенсионер', 'инвалид', 'многодетный'],
                'безопасность': ['преступность', 'дтп', 'пожар', 'освещение', 'камера',
                                 'охрана', 'полиция', 'скорая', 'происшествие']
            }

            self.problem_verbs = {
                'разрушать', 'отсутствовать', 'повреждать', 'закрывать', 'прерывать',
                'загрязнять', 'шуметь', 'переполнять', 'задерживать', 'нарушать',
                'ухудшать', 'портиться', 'ломаться', 'выходить из строя', 'создавать проблему'
            }

            self.logger.info("UrbanKnowledgeGraph инициализирован успешно")
            self.logger.info("=" * 60)

    def _setup_logger(self, log_level: str) -> logging.Logger:
            """Настройка логирования"""
            logger = logging.getLogger("UrbanKnowledgeGraph")
            logger.setLevel(getattr(logging, log_level))

            if not logger.handlers:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )

                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

            return logger

    def build_graph(self) -> nx.MultiDiGraph:
            """
            Построение графа знаний из отношений

            Returns:
                Построенный граф NetworkX
            """
            self.logger.info("Начало построения графа знаний")
            start_time = datetime.now()

            # Очистка графа
            self.graph.clear()

            # Добавление узлов и ребер
            nodes_added = set()
            edges_count = 0

            for idx, row in self.relations_df.iterrows():
                subject = row['Субъект']
                verb = row['Связь']
                obj = row['Объект']

                # Добавление узлов
                if subject not in nodes_added:
                    self.graph.add_node(subject, type='субъект', label=subject)
                    nodes_added.add(subject)

                if obj not in nodes_added:
                    self.graph.add_node(obj, type='объект', label=obj)
                    nodes_added.add(obj)

                # Добавление ребра
                self.graph.add_edge(subject, obj,
                                    relation=verb,
                                    weight=1,
                                    label=verb)
                edges_count += 1

            processing_time = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"Граф построен успешно")
            self.logger.info(f"  - Узлов: {self.graph.number_of_nodes()}")
            self.logger.info(f"  - Ребер: {self.graph.number_of_edges()}")
            self.logger.info(f"  - Время построения: {processing_time:.2f} секунд")

            return self.graph

    def analyze_communities(self) -> Dict:
            """
            Анализ сообществ в графе

            Returns:
                Словарь с информацией о сообществах
            """
            self.logger.info("Анализ сообществ в графе")

            if self.graph.number_of_nodes() == 0:
                self.logger.warning("Граф пустой")
                return {}

            # Преобразование в ненаправленный граф для анализа сообществ
            undirected_graph = self.graph.to_undirected()

            try:
                # Пробуем разные методы анализа сообществ
                communities = {}

                # Метод 1: Используем greedy_modularity_communities из networkx
                try:
                    from networkx.algorithms.community import greedy_modularity_communities
                    communities_list = list(greedy_modularity_communities(undirected_graph))
                    communities = {i: list(comm) for i, comm in enumerate(communities_list)}
                    method = "greedy_modularity"

                except ImportError:
                    # Метод 2: Используем connected_components как fallback
                    components = list(nx.connected_components(undirected_graph))
                    communities = {i: list(comp) for i, comp in enumerate(components)}
                    method = "connected_components"

                # Анализ сообществ
                community_stats = []
                for comm_id, nodes in communities.items():
                    if len(nodes) > 1:  # Игнорируем изолированные узлы
                        # Фильтрация проблем в сообществе
                        community_problems = []
                        for node in nodes:
                            if hasattr(node, 'startswith'):
                                # Проверяем, является ли узел объектом в отношениях
                                mask = self.relations_df['Объект'] == node
                                if mask.any():
                                    problem_row = self.relations_df[mask]
                                    if not problem_row.empty:
                                        related_verbs = problem_row['Связь'].unique().tolist()
                                        problem_type = self._classify_problem(node, related_verbs)
                                        if problem_type != 'другое':
                                            community_problems.append(node)

                        community_stats.append({
                            'Сообщество': comm_id,
                            'Размер': len(nodes),
                            'Проблемы': community_problems,
                            'Количество_проблем': len(community_problems),
                            'Узлы': nodes[:10]  # первые 10 узлов
                        })

                if community_stats:
                    community_stats_df = pd.DataFrame(community_stats)
                    community_stats_df = community_stats_df.sort_values('Размер', ascending=False)

                    self.logger.info(f"Обнаружено {len(communities)} сообществ (метод: {method})")
                    self.logger.info("Топ-5 самых больших сообществ:")
                    for idx, row in community_stats_df.head(5).iterrows():
                        self.logger.info(f"  Сообщество {row['Сообщество']}: "
                                         f"{row['Размер']} узлов, "
                                         f"{row['Количество_проблем']} проблем")

                    return {
                        'communities': communities,
                        'stats': community_stats_df,
                        'method': method
                    }
                else:
                    self.logger.warning("Нет сообществ для анализа")
                    return {}

            except Exception as e:
                self.logger.warning(f"Не удалось выполнить анализ сообществ: {e}")
                return {}

        # Остальные методы остаются без изменений...

    def calculate_density(self) -> Dict[str, float]:
        """
        Расчет плотности графа

        Returns:
            Словарь с различными метриками плотности
        """
        self.logger.info("Расчет плотности графа")

        if self.graph.number_of_nodes() == 0:
            self.logger.warning("Граф пустой, невозможно рассчитать плотность")
            return {'density': 0.0, 'directed_density': 0.0}

        # Плотность для ненаправленного графа
        undirected_graph = self.graph.to_undirected()
        n = undirected_graph.number_of_nodes()
        m = undirected_graph.number_of_edges()

        if n < 2:
            density = 0.0
        else:
            max_edges = n * (n - 1) / 2
            density = m / max_edges

        # Плотность для направленного графа
        n_directed = self.graph.number_of_nodes()
        m_directed = self.graph.number_of_edges()

        if n_directed < 2:
            directed_density = 0.0
        else:
            max_directed_edges = n_directed * (n_directed - 1)
            directed_density = m_directed / max_directed_edges

        # Сохранение метрик
        self.metrics['density'] = density
        self.metrics['directed_density'] = directed_density
        self.metrics['edges_per_node'] = m_directed / n_directed if n_directed > 0 else 0

        self.logger.info(f"Плотность графа:")
        self.logger.info(f"  - Плотность (ненаправленный): {density:.4f}")
        self.logger.info(f"  - Плотность (направленный): {directed_density:.4f}")
        self.logger.info(f"  - Среднее ребер на узел: {self.metrics['edges_per_node']:.2f}")

        return {
            'density': density,
            'directed_density': directed_density,
            'edges_per_node': self.metrics['edges_per_node']
        }

    def calculate_centrality(self, top_n: int = 20) -> Dict[str, pd.DataFrame]:
        """
        Расчет центральности узлов

        Args:
            top_n: Количество топ-узлов для вывода

        Returns:
            Словарь с DataFrames различных метрик центральности
        """
        self.logger.info("Расчет центральности узлов")

        if self.graph.number_of_nodes() == 0:
            self.logger.warning("Граф пустой, невозможно рассчитать центральность")
            return {}

        centrality_metrics = {}

        # 1. Степень центральность (Degree Centrality)
        degree_centrality = nx.degree_centrality(self.graph)
        in_degree_centrality = nx.in_degree_centrality(self.graph)
        out_degree_centrality = nx.out_degree_centrality(self.graph)

        # 2. Посредническая центральность (Betweenness Centrality)
        betweenness_centrality = nx.betweenness_centrality(self.graph, normalized=True)

        # 3. Близостная центральность (Closeness Centrality)
        closeness_centrality = nx.closeness_centrality(self.graph)

        # 4. Центральность по собственному вектору (Eigenvector Centrality)
        try:
            eigenvector_centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)
        except:
            self.logger.warning("Не удалось рассчитать eigenvector centrality")
            eigenvector_centrality = {node: 0 for node in self.graph.nodes()}

        # Создание DataFrame с метриками
        centrality_data = []
        for node in self.graph.nodes():
            centrality_data.append({
                'Узел': node,
                'Тип': self.graph.nodes[node].get('type', 'неизвестно'),
                'Degree': degree_centrality.get(node, 0),
                'In_Degree': in_degree_centrality.get(node, 0),
                'Out_Degree': out_degree_centrality.get(node, 0),
                'Betweenness': betweenness_centrality.get(node, 0),
                'Closeness': closeness_centrality.get(node, 0),
                'Eigenvector': eigenvector_centrality.get(node, 0),
                'Степень': self.graph.degree(node)
            })

        centrality_df = pd.DataFrame(centrality_data)

        # Сохранение в атрибутах класса
        self.centrality_df = centrality_df

        # Топ-узлы по каждой метрике
        centrality_metrics['degree_top'] = centrality_df.nlargest(top_n, 'Degree')
        centrality_metrics['betweenness_top'] = centrality_df.nlargest(top_n, 'Betweenness')
        centrality_metrics['closeness_top'] = centrality_df.nlargest(top_n, 'Closeness')
        centrality_metrics['eigenvector_top'] = centrality_df.nlargest(top_n, 'Eigenvector')

        # Логирование результатов
        self.logger.info("Топ-10 узлов по степени центральности:")
        for idx, row in centrality_metrics['degree_top'].head(10).iterrows():
            self.logger.info(f"  {row['Узел']}: {row['Degree']:.4f} (степень: {row['Степень']})")

        self.logger.info("Топ-10 узлов по посреднической центральности:")
        for idx, row in centrality_metrics['betweenness_top'].head(10).iterrows():
            self.logger.info(f"  {row['Узел']}: {row['Betweenness']:.4f}")

        return centrality_metrics




    def identify_problems(self, min_frequency: int = 2) -> pd.DataFrame:
        """
        Идентификация городских проблем + оценка комплексности каждой проблемы
        """
        STOP_PROBLEMS = {
            "дело", "внимание", "проблема", "решение",
            "работа", "место", "состояние", "мера",
            "срок", "город", "вопрос", "факт", "случай"
        }
        self.logger.info("Идентификация городских проблем")

        if not hasattr(self, 'relations_df') or self.relations_df.empty:
            self.logger.warning("Нет данных об отношениях")
            return pd.DataFrame()

        object_counts = self.relations_df['Объект'].value_counts()
        problem_candidates = []

        for obj, count in object_counts.items():
            if count < min_frequency:
                continue
            if obj.lower() in STOP_PROBLEMS:
                continue    
            # ---- базовая логика (ТВОЯ, без изменений) ----
            related_rows = self.relations_df[self.relations_df['Объект'] == obj]

            related_subjects = related_rows['Субъект'].unique()
            related_verbs = related_rows['Связь'].unique().tolist()

            problem_type = self._classify_problem(obj, related_verbs)
            importance_score = self._calculate_problem_importance(
                obj, count, related_subjects.tolist(), related_verbs
            )

            # ---- NEW: локальный подграф проблемы ----
            nodes = set(related_subjects) | {obj}
            subgraph = self.graph.subgraph(nodes).copy()

            relations_count = len(related_rows)
            unique_entities = len(nodes)
            unique_actions = len(related_verbs)
            subgraph_density = nx.density(subgraph) if subgraph.number_of_nodes() > 1 else 0.0
            if unique_actions < 2 or unique_entities < 2:
                continue
            # ---- NEW: complexity_score ----
            scorer = ComplexProblemScorer(
                frequency=count,
                unique_entities=unique_entities,
                unique_actions=unique_actions,
                subgraph_density=subgraph_density,
                relations_count=relations_count
            )

            complexity_score = scorer.compute()

            problem_candidates.append({
                'Проблема': obj,
                'Тип_проблемы': problem_type,
                'Частота_упоминаний': count,
                'Количество_субъектов': len(related_subjects),
                'Количество_действий': unique_actions,            
                'Количество_связей': relations_count,             
                'Плотность_подграфа': round(subgraph_density, 4), 
                'Важность': importance_score,
                'Complexity_score': complexity_score,             

                # Центральности оставляем
                'Центральность_степени': self.centrality_df[
                    self.centrality_df['Узел'] == obj
                ]['Degree'].values[0]
                if hasattr(self, 'centrality_df') and obj in self.centrality_df['Узел'].values else 0,

                'Центральность_посредническая': self.centrality_df[
                    self.centrality_df['Узел'] == obj
                ]['Betweenness'].values[0]
                if hasattr(self, 'centrality_df') and obj in self.centrality_df['Узел'].values else 0
            })

        if not problem_candidates:
            self.logger.warning("Не удалось идентифицировать проблемы")
            return pd.DataFrame()

        problems_df = pd.DataFrame(problem_candidates)

        # сортировка — ТЕПЕРЬ по комплексности
        problems_df = problems_df.sort_values(
            by='Complexity_score', ascending=False
        )

        self.problems = problems_df.to_dict('records')

        self.logger.info(f"Идентифицировано {len(problems_df)} городских проблем")

        self.logger.info("Топ-10 комплексных проблем:")
        for _, row in problems_df.head(10).iterrows():
            self.logger.info(
                f"  {row['Проблема']} | "
                f"complexity={row['Complexity_score']:.2f} | "
                f"freq={row['Частота_упоминаний']}"
            )

        return problems_df


    def _classify_problem(self, problem: str, verbs: List[str]) -> str:
        """Классификация проблемы по типу"""
        problem_lower = problem.lower()

        for category, keywords in self.problem_keywords.items():
            if any(keyword in problem_lower for keyword in keywords):
                return category

        # Дополнительная проверка по глаголам
        if any(verb in self.problem_verbs for verb in verbs):
            return 'проблемная_ситуация'

        return 'другое'

    def _calculate_problem_importance(self, problem: str, frequency: int,
                                      subjects: List[str], verbs: List[str]) -> float:
        """Расчет важности проблемы"""
        importance = 0.0

        # 1. Частота упоминаний (нормализованная)
        max_freq = self.relations_df['Объект'].value_counts().max()
        importance += (frequency / max_freq) * 0.4 if max_freq > 0 else 0

        # 2. Количество вовлеченных субъектов
        max_subjects = len(self.relations_df['Субъект'].unique())
        importance += (len(subjects) / max_subjects) * 0.3 if max_subjects > 0 else 0

        # 3. Критичность действий
        # Проверяем, что verbs не пустой и является списком/массивом
        if verbs is not None and len(verbs) > 0:
            # Преобразуем в список, если это массив
            if hasattr(verbs, 'tolist'):
                verbs_list = verbs.tolist()
            else:
                verbs_list = list(verbs)

            critical_verbs = len([v for v in verbs_list if v in self.problem_verbs])
            importance += (critical_verbs / len(verbs_list)) * 0.3

        return importance

    def visualize_graph(self, top_problems: int = 15, figsize: Tuple = (15, 10)):
        """
        Визуализация графа с выделением проблем

        Args:
            top_problems: Количество топ-проблем для визуализации
            figsize: Размер фигуры
        """
        self.logger.info(f"Визуализация графа (топ-{top_problems} проблем)")

        if self.graph.number_of_nodes() == 0:
            self.logger.warning("Граф пустой, невозможна визуализация")
            return

        # Получение топ-проблем
        if not hasattr(self, 'problems') or len(self.problems) == 0:
            problems_df = self.identify_problems()
        else:
            problems_df = pd.DataFrame(self.problems)

        if len(problems_df) == 0:
            self.logger.warning("Нет проблем для визуализации")
            return

        top_problems_list = problems_df.head(top_problems)['Проблема'].tolist()

        # Создание подграфа с топ-проблемами и связанными узлами
        nodes_to_include = set(top_problems_list)

        for problem in top_problems_list:
            # Добавляем соседей проблем
            if problem in self.graph:
                neighbors = list(self.graph.neighbors(problem)) + \
                            list(self.graph.predecessors(problem))
                nodes_to_include.update(neighbors)

        subgraph = self.graph.subgraph(nodes_to_include)

        # Визуализация
        plt.figure(figsize=figsize)

        # Позиционирование узлов
        pos = nx.spring_layout(subgraph, k=1, iterations=50)

        # Разделение узлов по типам
        problem_nodes = [n for n in subgraph.nodes() if n in top_problems_list]
        subject_nodes = [n for n in subgraph.nodes()
                         if n not in top_problems_list and
                         self.graph.nodes[n].get('type') == 'субъект']
        other_nodes = [n for n in subgraph.nodes()
                       if n not in top_problems_list and
                       n not in subject_nodes]

        # Размер узлов на основе центральности
        node_sizes = []
        for node in subgraph.nodes():
            if node in self.centrality_df['Узел'].values:
                centrality = self.centrality_df[
                    self.centrality_df['Узел'] == node
                    ]['Degree'].values[0]
                node_sizes.append(300 + centrality * 5000)
            else:
                node_sizes.append(300)

        # Рисование графа
        nx.draw_networkx_nodes(subgraph, pos, nodelist=problem_nodes,
                               node_color='red', node_size=[node_sizes[list(subgraph.nodes()).index(n)]
                                                            for n in problem_nodes],
                               alpha=0.8, label='Проблемы')
        nx.draw_networkx_nodes(subgraph, pos, nodelist=subject_nodes,
                               node_color='blue', node_size=[node_sizes[list(subgraph.nodes()).index(n)]
                                                             for n in subject_nodes],
                               alpha=0.6, label='Субъекты')
        nx.draw_networkx_nodes(subgraph, pos, nodelist=other_nodes,
                               node_color='gray', node_size=[node_sizes[list(subgraph.nodes()).index(n)]
                                                             for n in other_nodes],
                               alpha=0.4, label='Другие')

        # Рисование ребер
        nx.draw_networkx_edges(subgraph, pos, alpha=0.3, arrows=True, arrowstyle='->')

        # Подписи узлов
        labels = {node: node for node in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=9,
                                font_family='sans-serif')

        plt.title(f'Граф городских проблем (топ-{top_problems})', fontsize=16)
        plt.legend(scatterpoints=1)
        plt.axis('off')

        # Сохранение графика
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"urban_problems_graph_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()

        self.logger.info(f"Граф сохранен как {filename}")

    def get_summary_report(self) -> Dict:
        """
        Генерация сводного отчета

        Returns:
            Словарь с ключевыми метриками
        """
        self.logger.info("Генерация сводного отчета")

        summary = {
            'Общие_метрики': {
                'Количество_отношений': len(self.relations_df),
                'Уникальные_субъекты': self.relations_df['Субъект'].nunique(),
                'Уникальные_объекты': self.relations_df['Объект'].nunique(),
                'Уникальные_связи': self.relations_df['Связь'].nunique()
            },
            'Метрики_графа': self.metrics.copy(),
            'Проблемы_обнаружены': len(self.problems) if hasattr(self, 'problems') else 0,
            'Топ_проблемы': []
        }

        # Добавление топ-5 проблем
        if hasattr(self, 'problems') and len(self.problems) > 0:
            problems_df = pd.DataFrame(self.problems)
            top_5 = problems_df.head(5)[['Проблема', 'Тип_проблемы', 'Важность',
                                         'Частота_упоминаний']].to_dict('records')
            summary['Топ_проблемы'] = top_5

        # Добавление топ-центральных узлов
        if hasattr(self, 'centrality_df'):
            top_central = self.centrality_df.nlargest(5, 'Degree')[['Узел', 'Degree']].to_dict('records')
            summary['Топ_центральные_узлы'] = top_central

        # Логирование отчета
        self.logger.info("Сводный отчет:")
        self.logger.info(f"  Общие метрики:")
        for key, value in summary['Общие_метрики'].items():
            self.logger.info(f"    {key}: {value}")

        self.logger.info(f"  Метрики графа:")
        for key, value in summary['Метрики_графа'].items():
            self.logger.info(f"    {key}: {value:.4f}")

        self.logger.info(f"  Обнаружено проблем: {summary['Проблемы_обнаружены']}")

        return summary