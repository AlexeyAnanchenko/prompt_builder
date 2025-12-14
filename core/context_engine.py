import re
import json
from collections import defaultdict
from typing import Dict, List, Any, Set, Optional, Tuple

from utils.logger import setup_logger
from core.masking import ContextMasker

logger = setup_logger(__name__)

# ==========================================
# 1. DB DATA LOADER (Индексация данных)
# ==========================================
class DbDataLoader:
    """
    Класс для загрузки и быстрой индексации "сырых" данных из БД.
    Превращает списки строк в словари {Primary_Key -> Row}.
    """
    def __init__(self, raw_data: Dict[str, List[Dict[str, Any]]]):
        # Основное хранилище: { 'table_name': { (pk_tuple): {row_data} } }
        self.db: Dict[str, Dict[Tuple[Any, ...], Dict[str, Any]]] = defaultdict(dict)
        # Кэш имен колонок для каждой таблицы
        self.table_cols: Dict[str, List[str]] = {} 
        
        # Определение полей Primary Key для каждой таблицы (hardcoded schema)
        self.pks: Dict[str, List[str]] = {
            'datasets': ['namespace_id', 'tenant_id', 'dataset_id'],
            'vertices': ['namespace_id', 'tenant_id', 'vertex_id'],
            'edges': ['namespace_id', 'tenant_id', 'edge_id'],
            'entities': ['namespace_id', 'tenant_id', 'entity_type'],
            'entity_properties': ['namespace_id', 'tenant_id', 'entity_type', 'property_id'],
            'tables': ['namespace_id', 'tenant_id', 'table_id'],
            'table_fields': ['namespace_id', 'tenant_id', 'table_id', 'entity_type', 'property_id'],
            'parameters': ['namespace_id', 'tenant_id', 'parameter_id'],
            'constraints': ['namespace_id', 'tenant_id', 'constraint_id'],
            'composed_constraints': ['namespace_id', 'tenant_id', 'constraint_id'],
            'filters': ['namespace_id', 'tenant_id', 'vertex_id', 'index'],
            'vertex_functions': ['namespace_id', 'tenant_id', 'vertex_id', 'entity_type', 'property_id'],
            'aggregation': ['namespace_id', 'tenant_id', 'aggregation_id'],
            'limitation': ['namespace_id', 'tenant_id', 'limitation_id'],
            'ordering': ['namespace_id', 'tenant_id', 'ordering_id'],
            'group_by': ['namespace_id', 'tenant_id', 'group_id', 'index'],
            'order_by': ['namespace_id', 'tenant_id', 'order_id', 'index'],
            'namespaces': ['namespace_id'],
            'tenants': ['tenant_id'],
            'clients': ['service_id', 'component_id'],
            'composed_entities': ['namespace_id', 'tenant_id', 'composed_entity', 'entity_type']
        }
        self._index_data(raw_data)
        total_records = sum(len(v) for v in self.db.values())
        logger.info(f"DbDataLoader проиндексировал {total_records} записей.")

    def _index_data(self, raw_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Превращает списки словарей в хэш-таблицы по Primary Key."""
        for table, rows in raw_data.items():
            if not rows: continue
            # Сохраняем имена колонок из первой строки
            self.table_cols[table] = list(rows[0].keys())
            for row in rows:
                try:
                    pk = self._get_pk_key(table, row)
                    self.db[table][pk] = row
                except Exception as e:
                    logger.warning(f"Ошибка индексации строки в {table}: {e}")

    def _get_pk_key(self, table_name: str, row: Dict[str, Any]) -> Tuple[str, ...]:
        """Формирует кортеж PK для строки."""
        if table_name in self.pks:
            # Приводим все части ключа к строке для надежности
            return tuple(str(row.get(k, '')) for k in self.pks[table_name])
        # Если для таблицы нет PK в конфиге, используем все значения (fallback)
        return tuple(row.values())


# ==========================================
# 2. CONTEXT RESOLVER (Граф зависимостей)
# ==========================================
class ContextResolver:
    """
    Класс для рекурсивного поиска зависимостей.
    Например: Если выбран Dataset -> нужно найти все его Vertices -> для каждой Vertex найти Table -> Entity -> Properties и т.д.
    """
    def __init__(self, loader: DbDataLoader):
        self.loader = loader
        # Результат работы: { 'table_name': {set_of_pks} }
        self.context: Dict[str, Set[Tuple]] = defaultdict(set)
        
        # Regex для поиска зависимостей в формулах
        self.prop_regex = re.compile(r'\b([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\b') # Entity.Property
        self.param_regex = re.compile(r'\{([a-zA-Z0-9_]+)\}') # {param}

    def resolve_by_dataset(self, dataset_id: str) -> bool:
        """Точка входа: Найти всё, что связано с Dataset."""
        found = False
        # Ищем во всех строках таблицы datasets (pk[2] == dataset_id)
        for pk, row in self.loader.db['datasets'].items():
            if pk[2] == dataset_id:
                self._add_dataset(pk)
                found = True
        return found
    
    def resolve_by_entity(self, entity_type: str) -> bool:
        """Точка входа: Найти всё, что связано с Entity."""
        found = False
        for pk, row in self.loader.db['entities'].items():
            if pk[2] == entity_type:
                self._add_entity(pk)
                self._add_all_properties_for_entity(pk)
                found = True
        return found

    # --- Внутренние методы рекурсивного обхода ---

    def _add_dataset(self, pk: Tuple):
        if pk in self.context['datasets']: return
        self.context['datasets'].add(pk)
        
        row = self.loader.db['datasets'][pk]
        # 1. Сканируем JSON конфиг датасета
        self._scan_json_config(row.get('config'))
        # 2. Добавляем ребра (edges)
        edges = row.get('edges')
        if edges:
            for edge_id in edges: self._find_and_add_edge(str(edge_id))

    def _find_and_add_edge(self, edge_id_str: str):
        for pk in self.loader.db['edges']:
            if str(pk[2]) == edge_id_str:
                self._add_edge(pk)
                return 

    def _add_edge(self, pk: Tuple):
        if pk in self.context['edges']: return
        self.context['edges'].add(pk)
        row = self.loader.db['edges'][pk]
        
        # Зависимости ребра: вершины source и target
        self._find_and_add_vertex(str(row.get('source_vertex')))
        self._find_and_add_vertex(str(row.get('target_vertex')))
        
        self._process_constraints_list(row.get('constraints'))
        self._scan_json_config(row.get('config'))
        self._scan_formula(row.get('condition')) 

    def _find_and_add_vertex(self, vertex_id_str: str):
        for pk in self.loader.db['vertices']:
            if str(pk[2]) == vertex_id_str:
                self._add_vertex(pk)
                return

    def _add_vertex(self, pk: Tuple):
        if pk in self.context['vertices']: return
        self.context['vertices'].add(pk)
        row = self.loader.db['vertices'][pk]
        
        v_type = row.get('vertex_type')
        config_obj = row.get('config')
        
        # Если вершина - это датасет или таблица, нужно найти их определения
        if v_type == 'dataset':
             conf = self._get_json(config_obj)
             if conf and 'dataset' in conf: self.resolve_by_dataset(conf['dataset'])
        elif v_type == 'table':
             conf = self._get_json(config_obj)
             if conf and 'table' in conf: self._find_and_add_table_by_id(conf['table'])
             
        self._process_constraints_list(row.get('constraints'))
        self._scan_json_config(config_obj)
        self._add_vertex_functions(pk)
        self._add_vertex_filters(pk)

    def _add_vertex_functions(self, vertex_pk: Tuple):
        for vf_pk, row in self.loader.db['vertex_functions'].items():
            # Связь по vertex_id (индекс 2 в PK)
            if str(vf_pk[2]) == str(vertex_pk[2]):
                if vf_pk not in self.context['vertex_functions']:
                    self.context['vertex_functions'].add(vf_pk)
                    self._scan_formula(row.get('calculation_func'))
                    self._scan_formula(row.get('aggregation_func'))
                    # Ссылка на свойство сущности
                    self._find_and_add_property(vf_pk[3], vf_pk[4])

    def _add_vertex_filters(self, vertex_pk: Tuple):
        for f_pk, row in self.loader.db['filters'].items():
            if str(f_pk[2]) == str(vertex_pk[2]):
                 if f_pk not in self.context['filters']:
                    self.context['filters'].add(f_pk)
                    self._scan_json_config(row.get('config'))

    def _find_and_add_table_by_id(self, table_id: str):
        found_pk = None
        for pk in self.loader.db['tables']:
            if str(pk[2]) == str(table_id):
                found_pk = pk
                break 
        if found_pk:
            if found_pk not in self.context['tables']:
                self.context['tables'].add(found_pk)
                self._add_table_fields(found_pk)

    def _add_table_fields(self, table_pk: Tuple):
        for tf_pk, row in self.loader.db['table_fields'].items():
             if str(tf_pk[2]) == str(table_pk[2]):
                 self.context['table_fields'].add(tf_pk)
                 self._find_and_add_property(tf_pk[3], tf_pk[4])

    def _process_constraints_list(self, constraints: Any):
        if not constraints or not isinstance(constraints, list): return
        for cid in constraints: self._find_and_add_constraint(int(cid))

    def _find_and_add_constraint(self, cid: int):
        # Обычные constraints
        for cpk in self.loader.db['constraints']:
            if int(cpk[2]) == cid:
                if cpk not in self.context['constraints']:
                    self.context['constraints'].add(cpk)
                    row = self.loader.db['constraints'][cpk]
                    self._scan_json_config(row.get('config'))
                    self._scan_formula(row.get('condition'))
                    if row.get('entity_type') and row.get('property_id'):
                        self._find_and_add_property(row['entity_type'], row['property_id'])
                return
        # Составные constraints
        for cpk in self.loader.db['composed_constraints']:
            if int(cpk[2]) == cid:
                if cpk not in self.context['composed_constraints']:
                    self.context['composed_constraints'].add(cpk)
                    row = self.loader.db['composed_constraints'][cpk]
                    self._process_constraints_list(row.get('constraints'))
                    self._scan_formula(row.get('condition'))
                return

    def _scan_json_config(self, config_obj: Any):
            """Рекурсивно ищет ссылки на сущности, параметры и т.д. внутри JSON."""
            data = self._get_json(config_obj)
            if not data: return
            
            def recursive_search(obj):
                if isinstance(obj, dict):
                    if 'entity' in obj and 'property' in obj:
                        self._find_and_add_property(obj['entity'], obj['property'])
                    if 'valueExpr' in obj:
                        self._scan_formula(obj['valueExpr'])
                    if 'parameter' in obj:
                        self._find_and_add_parameter(obj['parameter'])
                    if 'dataset' in obj:
                        self.resolve_by_dataset(obj['dataset'])
                    
                    for key in ['aggregation', 'limitation', 'ordering']:
                        if key in obj:
                            self._find_and_add_obj(key, obj[key])

                    if 'table' in obj:
                        self._find_and_add_table_by_id(obj['table'])
                        
                    for k, v in obj.items():
                        recursive_search(v)
                elif isinstance(obj, list):
                    for item in obj: recursive_search(item)
                    
            recursive_search(data)

    def _find_and_add_parameter(self, param_id: str):
        for pk in self.loader.db['parameters']:
            if str(pk[2]) == str(param_id): 
                self.context['parameters'].add(pk)

    def _find_and_add_obj(self, table: str, obj_id: str):
        """Универсальный метод добавления объекта по ID."""
        for pk in self.loader.db[table]:
            if str(pk[-1]) == str(obj_id): 
                if pk not in self.context[table]:
                    self.context[table].add(pk)
                    
                    row = self.loader.db[table][pk]
                    # Если добавляем limitation, нужно просканировать формулы внутри
                    if table == 'limitation':
                        self._scan_formula(row.get('total_limit'))
                        self._scan_formula(row.get('group_limit'))

    def _scan_formula(self, formula: Optional[str]):
        """Парсит формулы для поиска зависимостей (Entity.Property, {param})."""
        if not formula: return
        
        # 1. SQL-style: Entity.Property
        matches = self.prop_regex.findall(formula)
        for entity_type, prop_id in matches:
            if self._is_valid_property(entity_type, prop_id):
                self._find_and_add_property(entity_type, prop_id)
        
        # 2. SQL-style Params: {param}
        params = self.param_regex.findall(formula)
        for p_id in params:
            self._find_and_add_parameter(p_id)

        # 3. Java-style Params: param != null
        self._scan_java_condition(formula)

    def _scan_java_condition(self, condition: str):
        """Ищет параметры, используемые без фигурных скобок (Java syntax)."""
        words = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', condition)
        ignore_keywords = {'null', 'true', 'false', 'equals', 'not', 'and', 'or', 'if', 'else', 'return'}
        
        candidates = set(words) - ignore_keywords
        if not candidates: return

        # Проверяем кандидатов в базе параметров
        for param_id in candidates:
             found = False
             for pk in self.loader.db['parameters']:
                 if pk[2] == param_id:
                     self.context['parameters'].add(pk)
                     found = True

    def _is_valid_property(self, entity: str, prop: str) -> bool:
        for pk in self.loader.db['entity_properties']:
            if pk[2] == entity and pk[3] == prop: return True
        return False

    def _find_and_add_property(self, entity: str, prop: str):
        for pk, row in self.loader.db['entity_properties'].items():
            if pk[2] == entity and pk[3] == prop:
                if pk not in self.context['entity_properties']:
                    self.context['entity_properties'].add(pk)
                    self._add_entity_from_property_pk(pk)
                    self._scan_formula(row.get('calculation_func'))
                    self._scan_formula(row.get('aggregation_func'))

    def _add_entity_from_property_pk(self, prop_pk: Tuple):
        """Добавляет родительскую сущность для свойства."""
        ns, tenant, entity_type, _ = prop_pk
        target_pk = (ns, tenant, entity_type)
        if target_pk in self.loader.db['entities']:
            self._add_entity_pk_direct(target_pk)
            return
        # Fallback на глобальный тенант (если пусто)
        if tenant != '':
            fallback_pk = (ns, '', entity_type)
            if fallback_pk in self.loader.db['entities']:
                self._add_entity_pk_direct(fallback_pk)

    def _add_entity(self, pk: Tuple):
        if pk in self.loader.db['entities']:
            self._add_entity_pk_direct(pk)
        else:
            if pk[1] != '':
                fallback = (pk[0], '', pk[2])
                if fallback in self.loader.db['entities']:
                    self._add_entity_pk_direct(fallback)

    def _add_entity_pk_direct(self, pk: Tuple):
        if pk not in self.context['entities']:
            self.context['entities'].add(pk)
            # Если сущность составная (Composed), добавляем родителя
            self._check_composed(pk[2])

    def _add_all_properties_for_entity(self, entity_pk: Tuple):
        for pk, row in self.loader.db['entity_properties'].items():
            if pk[2] == entity_pk[2]:
                self._find_and_add_property(pk[2], pk[3])

    def _check_composed(self, entity_type: str):
        for pk, row in self.loader.db.get('composed_entities', {}).items():
            if pk[2] == entity_type:
                if pk not in self.context['composed_entities']:
                    self.context['composed_entities'].add(pk)
                    parent_type = pk[3]
                    ns, tenant = pk[0], pk[1]
                    candidates = [(ns, tenant, parent_type), (ns, '', parent_type)]
                    for cand in candidates:
                        if cand in self.loader.db['entities']:
                            self._add_entity_pk_direct(cand)
                            self._add_all_properties_for_entity(cand)
                            break
    def _get_json(self, obj: Any) -> Any:
        if isinstance(obj, dict): return obj
        if isinstance(obj, str):
            try: return json.loads(obj)
            except: return None
        return None

# ==========================================
# 3. OUTPUT GENERATOR (SQL Генерация)
# ==========================================

class OutputGenerator:
    """
    Класс, отвечающий за формирование INSERT SQL выражений на основе собранного контекста.
    Также применяет маскирование, если передан masker.
    """
    def __init__(self, loader: DbDataLoader, context: Dict[str, Set[tuple]], masker: Optional[ContextMasker] = None):
        self.loader = loader
        self.context = context
        self.masker = masker
        
        # Ссылка на конфигурацию маскирования (из schema_config.py или hardcoded)
        # Здесь продублируем для наглядности логики, но в идеале импортировать.
        self.field_mapping = {
            'tenants': {'tenant_id': 'TEN', 'tenant_name': 'TEN_NAME'},
            'entities': {'tenant_id': 'TEN', 'entity_type': 'ENT', 'entity_name': 'ENT_NAME'},
            'composed_entities': {'tenant_id': 'TEN', 'composed_entity': 'ENT', 'entity_type': 'ENT'},
            'entity_properties': {
                'tenant_id': 'TEN', 'entity_type': 'ENT', 'property_id': 'P',
                'calculation_func': 'FORMULA', 'aggregation_func': 'FORMULA', 'conversion_func': 'FORMULA'
            },
            'parameters': {'tenant_id': 'TEN', 'parameter_id': 'PARAM', 'request_path': 'ARRAY_PATH'},
            'datasets': {'tenant_id': 'TEN', 'dataset_id': 'DS', 'entity_type': 'ENT', 'config': 'JSON'},
            'tables': {'tenant_id': 'TEN', 'table_id': 'TBL', 'physical_name': 'DB.TBL'},
            'table_fields': {'tenant_id': 'TEN', 'table_id': 'TBL', 'entity_type': 'ENT', 'property_id': 'P', 'field_name': 'COL'},
            'vertices': {'tenant_id': 'TEN', 'config': 'JSON', 'constraints': 'JSON'},
            'edges': {'tenant_id': 'TEN', 'condition': 'FORMULA', 'config': 'JSON'},
            'vertex_functions': {'tenant_id': 'TEN', 'entity_type': 'ENT', 'property_id': 'P', 'calculation_func': 'FORMULA', 'aggregation_func': 'FORMULA'},
            'constraints': {'tenant_id': 'TEN', 'entity_type': 'ENT', 'property_id': 'P', 'config': 'JSON', 'condition': 'FORMULA'},
            'composed_constraints': {'tenant_id': 'TEN', 'condition': 'FORMULA'},
            'filters': {'tenant_id': 'TEN', 'config': 'JSON'},
            'aggregation': {'tenant_id': 'TEN', 'aggregation_id': 'AGG'},
            'limitation': {'tenant_id': 'TEN', 'limitation_id': 'LIM', 'total_limit': 'FORMULA'},
            'ordering': {'tenant_id': 'TEN', 'ordering_id': 'ORD'},
            'group_by': {'tenant_id': 'TEN', 'entity_type': 'ENT', 'property_id': 'P'},
            'order_by': {'tenant_id': 'TEN', 'entity_type': 'ENT', 'property_id': 'P'}
        }

    def _ensure_tenants_exist(self):
        """Гарантирует, что определения тенантов попадут в SQL, если они используются в других таблицах."""
        used_ids = set()
        for table, pks in self.context.items():
            if table in ['namespaces', 'tenants', 'clients']: continue
            for pk in pks:
                if len(pk) >= 2 and pk[1]: # pk[1] is tenant_id
                    used_ids.add(pk[1])
        
        if 'tenants' not in self.context:
            self.context['tenants'] = set()
            
        used_ids.add('') # Дефолтный тенант
            
        for tid in used_ids:
            pk = (tid,)
            if pk in self.loader.db.get('tenants', {}):
                self.context['tenants'].add(pk)

    def _prefill_known_parameters(self):
        """Собирает известные параметры для маскера (чтобы он видел их в Java-формулах)."""
        if not self.masker: return
        
        param_ids = set()
        for pk in self.context.get('parameters', set()):
            # pk = (ns, tenant, param_id)
            param_ids.add(pk[2])
            
        self.masker.set_known_parameters(param_ids)
        
        # Сразу регистрируем их в маскере, чтобы получить маски (PARAM_1)
        for pid in param_ids:
            self.masker.register(pid, 'PARAM')

    def generate_sql(self) -> str:
        """Генерирует финальный SQL скрипт."""
        lines = []
        lines.append("SET SEARCH_PATH to qe_config;\n")
        
        self._ensure_tenants_exist()
        self._prefill_known_parameters()
        
        # Порядок вставки важен для целостности (FK constraint logic)
        order = [
            'namespaces', 'tenants', 'clients',
            'parameters',
            'entities', 'composed_entities', 'entity_properties',
            'tables', 'table_fields',
            'aggregation', 'limitation', 'ordering', 'group_by', 'order_by',
            'constraints', 'composed_constraints',
            'vertices', 'vertex_functions', 'edges', 'filters',
            'datasets'
        ]
        
        for table in order:
            pks = self.context.get(table, set())
            if not pks: continue
            
            lines.append(f"-- {table} ({len(pks)})")
            
            # Получаем колонки таблицы
            cols = self.loader.table_cols.get(table, [])
            if not cols and pks:
                first = next(iter(pks))
                cols = list(self.loader.db[table][first].keys())
                
            table_map = self.field_mapping.get(table, {})
            sorted_pks = sorted(list(pks))
            values_rows = []
            
            for pk in sorted_pks:
                # ЗАЩИТА ОТ ОШИБОК: Если одна запись битая, пропускаем её, а не падаем
                try:
                    if pk not in self.loader.db[table]: continue
                    row = self.loader.db[table][pk]
                    
                    vals = []
                    for col in cols:
                        val = row.get(col)
                        val_to_write = val
                        
                        # --- ЛОГИКА МАСКИРОВАНИЯ ---
                        if self.masker and val is not None:
                            action = table_map.get(col)
                            
                            if action == 'JSON':
                                # Парсим -> Маскируем -> Сериализуем обратно
                                try:
                                    if isinstance(val, str):
                                        json_obj = json.loads(val)
                                        masked_obj = self.masker.mask_json(json_obj)
                                        val_to_write = json.dumps(masked_obj, ensure_ascii=False)
                                    elif isinstance(val, (dict, list)):
                                        masked_obj = self.masker.mask_json(val)
                                        val_to_write = json.dumps(masked_obj, ensure_ascii=False)
                                except:
                                    # Если не парсится JSON, маскируем как текст
                                    val_to_write = self.masker.mask_text(str(val))
                                    
                            elif action == 'FORMULA':
                                if isinstance(val, str):
                                    val_to_write = self.masker.mask_formula(val)
                                    
                            elif action == 'ARRAY_PATH':
                                # Обработка SQL-массивов '{a,b}'
                                arr = self._parse_array(val)
                                masked_arr = [self.masker.register(x, 'PATH') for x in arr]
                                val_to_write = masked_arr 
                                
                            elif action and action not in ['JSON', 'FORMULA', 'ARRAY_PATH']:
                                # Прямая замена по категории
                                if isinstance(val, str) and val:
                                    val_to_write = self.masker.register(val, action)
                        
                        vals.append(self._format_val(val_to_write))
                    
                    # Форматирование вывода SQL
                    complex_tables = ['entity_properties', 'vertex_functions', 'limitation']
                    if table in complex_tables:
                        row_str = self._format_row_pretty(vals)
                    else:
                        row_str = f"({', '.join(vals)})"
                    
                    values_rows.append(row_str)
                    
                except Exception as e:
                    logger.error(f"Ошибка генерации строки для {table} pk={pk}: {e}")
            
            if values_rows:
                header = f"INSERT INTO {table} ({', '.join(cols)}) VALUES"
                body = ",\n".join(values_rows)
                lines.append(f"{header}\n{body};")
            
            lines.append("")
            
        return "\n".join(lines)

    def _parse_array(self, val: Any) -> List[str]:
        """Парсит строковое представление массива PostgreSQL."""
        if isinstance(val, list): return [str(x) for x in val if x]
        if not isinstance(val, str): return []
        val = val.strip()
        if val.startswith('{') and val.endswith('}'):
            content = val[1:-1]
            if not content: return []
            parts = content.split(',')
            res = []
            for p in parts:
                p = p.strip()
                # Удаляем кавычки
                if len(p) >= 2 and (p[0] in '"\'' and p[-1] in '"\''):
                    p = p[1:-1]
                if p: res.append(p)
            return res
        return []

    def _format_val(self, val: Any) -> str:
        """Форматирует значение для вставки в SQL (экранирование кавычек)."""
        if val is None: return "null"
        if isinstance(val, bool): return "true" if val else "false"
        if isinstance(val, (int, float)): return str(val)
        
        if isinstance(val, list):
            # Формируем SQL массив: '{val1, val2}'
            safe_list = [str(x) for x in val if x is not None]
            formatted_list = []
            for x in safe_list:
                escaped = x.replace("'", "''") 
                formatted_list.append(f'"{x}"') # В массивах Postgres строки в двойных кавычках
            return "'{" + ", ".join(formatted_list) + "}'" 
            
        if isinstance(val, dict):
            json_str = json.dumps(val, ensure_ascii=False)
            escaped = json_str.replace("'", "''")
            return f"'{escaped}'"
            
        if isinstance(val, str):
            escaped = val.replace("'", "''")
            return f"'{escaped}'"
            
        return f"'{str(val)}'"

    def _format_row_pretty(self, vals: List[str]) -> str:
        """Красивое форматирование VALUES (...) с переносами строк для читаемости."""
        lines = []
        current_line = "  "
        VERTICAL_START = 5 # Начинать перенос строк после 5-й колонки
        
        for i, val in enumerate(vals):
            is_last = (i == len(vals) - 1)
            suffix = "" if is_last else ", "
            
            # Если значение многострочное (формулы)
            if '\n' in val:
                if current_line.strip():
                    lines.append(current_line.rstrip())
                    current_line = "  "
                replace_space_val = val.replace("    ", "  ")
                lines.append(f"  {replace_space_val}{suffix}")
                continue

            if i >= VERTICAL_START:
                if current_line.strip():
                    lines.append(current_line.rstrip())
                lines.append(f"  {val}{suffix}")
                current_line = ""
                continue

            # Компактная запись, пока влезает в строку
            if len(current_line) + len(val) > 120:
                 lines.append(current_line.rstrip())
                 current_line = f"  {val}{suffix}"
            else:
                 current_line += f"{val}{suffix}"
        
        if current_line.strip():
            lines.append(current_line.rstrip())
            
        return "(\n" + "\n".join(lines) + "\n)"