import re
import json
import datetime
from collections import defaultdict
from typing import Dict, List, Any, Set, Optional, Union

from utils.logger import setup_logger
from core.masking import ContextMasker

logger = setup_logger(__name__)

# ==========================================
# 1. DB DATA LOADER
# ==========================================
class DbDataLoader:
    def __init__(self, raw_data: Dict[str, List[Dict[str, Any]]]):
        self.db: Dict[str, Dict[Any, Dict[str, Any]]] = defaultdict(dict)
        self.table_cols: Dict[str, List[str]] = {} 
        self.pks = {
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
        logger.info(f"DbDataLoader initialized with {sum(len(v) for v in self.db.values())} records.")

    def _index_data(self, raw_data: Dict[str, List[Dict[str, Any]]]):
        for table, rows in raw_data.items():
            if not rows: continue
            self.table_cols[table] = list(rows[0].keys())
            for row in rows:
                pk = self._get_pk_key(table, row)
                self.db[table][pk] = row

    def _get_pk_key(self, table_name: str, row: Dict[str, Any]):
        if table_name in self.pks:
            return tuple(str(row.get(k, '')) for k in self.pks[table_name])
        return tuple(row.values())


# ==========================================
# 2. CONTEXT RESOLVER
# ==========================================
class ContextResolver:
    def __init__(self, loader: DbDataLoader):
        self.loader = loader
        self.context: Dict[str, Set[tuple]] = defaultdict(set)
        self.prop_regex = re.compile(r'\b([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\b')
        self.param_regex = re.compile(r'\{([a-zA-Z0-9_]+)\}')

    def resolve_by_dataset(self, dataset_id: str):
        found = False
        for pk, row in self.loader.db['datasets'].items():
            if pk[2] == dataset_id: 
                self._add_dataset(pk)
                found = True
        return found
    
    def resolve_by_entity(self, entity_type: str):
        found = False
        for pk, row in self.loader.db['entities'].items():
            if pk[2] == entity_type:
                self._add_entity(pk)
                self._add_all_properties_for_entity(pk)
                found = True
        return found

    def _add_dataset(self, pk):
        if pk in self.context['datasets']: return
        self.context['datasets'].add(pk)
        row = self.loader.db['datasets'][pk]
        self._scan_json_config(row.get('config'))
        edges = row.get('edges')
        if edges:
            for edge_id in edges: self._find_and_add_edge(str(edge_id))

    def _find_and_add_edge(self, edge_id_str):
        for pk in self.loader.db['edges']:
            if str(pk[2]) == edge_id_str:
                self._add_edge(pk)
                return 

    def _add_edge(self, pk):
        if pk in self.context['edges']: return
        self.context['edges'].add(pk)
        row = self.loader.db['edges'][pk]
        self._find_and_add_vertex(str(row.get('source_vertex')))
        self._find_and_add_vertex(str(row.get('target_vertex')))
        self._process_constraints_list(row.get('constraints'))
        self._scan_json_config(row.get('config'))

    def _find_and_add_vertex(self, vertex_id_str):
        for pk in self.loader.db['vertices']:
            if str(pk[2]) == vertex_id_str:
                self._add_vertex(pk)
                return

    def _add_vertex(self, pk):
        if pk in self.context['vertices']: return
        self.context['vertices'].add(pk)
        row = self.loader.db['vertices'][pk]
        v_type = row.get('vertex_type')
        config_obj = row.get('config')
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

    def _add_vertex_functions(self, vertex_pk):
        for vf_pk, row in self.loader.db['vertex_functions'].items():
            if str(vf_pk[2]) == str(vertex_pk[2]):
                if vf_pk not in self.context['vertex_functions']:
                    self.context['vertex_functions'].add(vf_pk)
                    self._scan_formula(row.get('calculation_func'))
                    self._scan_formula(row.get('aggregation_func'))
                    self._find_and_add_property(vf_pk[3], vf_pk[4])

    def _add_vertex_filters(self, vertex_pk):
        for f_pk, row in self.loader.db['filters'].items():
            if str(f_pk[2]) == str(vertex_pk[2]):
                 if f_pk not in self.context['filters']:
                    self.context['filters'].add(f_pk)
                    self._scan_json_config(row.get('config'))

    def _find_and_add_table_by_id(self, table_id):
        found_pk = None
        for pk in self.loader.db['tables']:
            if str(pk[2]) == str(table_id):
                found_pk = pk
                break 
        if found_pk:
            if found_pk not in self.context['tables']:
                self.context['tables'].add(found_pk)
                self._add_table_fields(found_pk)

    def _add_table_fields(self, table_pk):
        for tf_pk, row in self.loader.db['table_fields'].items():
             if str(tf_pk[2]) == str(table_pk[2]):
                 self.context['table_fields'].add(tf_pk)
                 self._find_and_add_property(tf_pk[3], tf_pk[4])

    def _process_constraints_list(self, constraints):
        if not constraints or not isinstance(constraints, list): return
        for cid in constraints: self._find_and_add_constraint(int(cid))

    def _find_and_add_constraint(self, cid):
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
        for cpk in self.loader.db['composed_constraints']:
            if int(cpk[2]) == cid:
                if cpk not in self.context['composed_constraints']:
                    self.context['composed_constraints'].add(cpk)
                    row = self.loader.db['composed_constraints'][cpk]
                    self._process_constraints_list(row.get('constraints'))
                    self._scan_formula(row.get('condition'))
                return

    def _scan_json_config(self, config_obj):
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

    def _find_and_add_parameter(self, param_id):
        for pk in self.loader.db['parameters']:
            if str(pk[2]) == str(param_id): 
                self.context['parameters'].add(pk)

    def _find_and_add_obj(self, table, obj_id):
        for pk in self.loader.db[table]:
            if str(pk[-1]) == str(obj_id): 
                self.context[table].add(pk)

    def _scan_formula(self, formula: Optional[str]):
        if not formula: return
        matches = self.prop_regex.findall(formula)
        for entity_type, prop_id in matches:
            if self._is_valid_property(entity_type, prop_id):
                self._find_and_add_property(entity_type, prop_id)
        params = self.param_regex.findall(formula)
        for p_id in params:
            self._find_and_add_parameter(p_id)

    def _is_valid_property(self, entity, prop):
        for pk in self.loader.db['entity_properties']:
            if pk[2] == entity and pk[3] == prop: return True
        return False

    def _find_and_add_property(self, entity, prop):
        for pk, row in self.loader.db['entity_properties'].items():
            if pk[2] == entity and pk[3] == prop:
                if pk not in self.context['entity_properties']:
                    self.context['entity_properties'].add(pk)
                    self._add_entity_from_property_pk(pk)
                    self._scan_formula(row.get('calculation_func'))
                    self._scan_formula(row.get('aggregation_func'))

    def _add_entity_from_property_pk(self, prop_pk):
        ns, tenant, entity_type, _ = prop_pk
        target_pk = (ns, tenant, entity_type)
        if target_pk in self.loader.db['entities']:
            self._add_entity_pk_direct(target_pk)
            return
        if tenant != '':
            fallback_pk = (ns, '', entity_type)
            if fallback_pk in self.loader.db['entities']:
                self._add_entity_pk_direct(fallback_pk)

    def _add_entity(self, pk):
        if pk in self.loader.db['entities']:
            self._add_entity_pk_direct(pk)
        else:
            if pk[1] != '':
                fallback = (pk[0], '', pk[2])
                if fallback in self.loader.db['entities']:
                    self._add_entity_pk_direct(fallback)

    def _add_entity_pk_direct(self, pk):
        if pk not in self.context['entities']:
            self.context['entities'].add(pk)
            self._check_composed(pk[2])

    def _add_all_properties_for_entity(self, entity_pk):
        for pk, row in self.loader.db['entity_properties'].items():
            if pk[2] == entity_pk[2]:
                self._find_and_add_property(pk[2], pk[3])

    def _check_composed(self, entity_type):
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
    def _get_json(self, obj):
        if isinstance(obj, dict): return obj
        if isinstance(obj, str):
            try: return json.loads(obj)
            except: return None
        return None

# ==========================================
# 3. OUTPUT GENERATOR
# ==========================================

class OutputGenerator:
    def __init__(self, loader: DbDataLoader, context: Dict[str, Set[tuple]], masker: Optional[ContextMasker] = None):
        self.loader = loader
        self.context = context
        self.masker = masker
        
        # Карта маскирования: Table -> Field -> Action/Category
        # Action может быть: 
        #   - строка 'CATEGORY': прямая замена через register(val, CATEGORY)
        #   - 'JSON': обработка через mask_json
        #   - 'FORMULA': обработка через mask_formula
        #   - 'ARRAY_PATH': обработка массива путей
        self.field_mapping = {
            'tenants': {
                'tenant_id': 'TEN',
                'tenant_name': 'TEN_NAME'
            },
            'entities': {
                'entity_type': 'ENT',
                'entity_name': 'ENT_NAME'
            },
            'composed_entities': {
                'composed_entity': 'ENT',
                'entity_type': 'ENT'
            },
            'entity_properties': {
                'entity_type': 'ENT',
                'property_id': 'P',
                'calculation_func': 'FORMULA',
                'aggregation_func': 'FORMULA',
                'conversion_func': 'FORMULA'
            },
            'parameters': {
                'parameter_id': 'PARAM',
                'request_path': 'ARRAY_PATH'
            },
            'datasets': {
                'dataset_id': 'DS',
                'entity_type': 'ENT',
                'config': 'JSON'
            },
            'tables': {
                'table_id': 'TBL',
                'physical_name': 'DB.TBL'
            },
            'table_fields': {
                'table_id': 'TBL',
                'entity_type': 'ENT',
                'property_id': 'P',
                'field_name': 'COL'
            },
            'vertices': {
                'config': 'JSON',
                'constraints': 'JSON' # constraints здесь часто просто список ID, но если JSON - сработает
            },
            'edges': {
                'condition': 'FORMULA',
                'config': 'JSON'
            },
            'vertex_functions': {
                'entity_type': 'ENT',
                'property_id': 'P',
                'calculation_func': 'FORMULA',
                'aggregation_func': 'FORMULA'
            },
            'constraints': {
                'entity_type': 'ENT',
                'property_id': 'P',
                'config': 'JSON',
                'condition': 'FORMULA'
            },
            'composed_constraints': {
                'condition': 'FORMULA'
            },
            'filters': {
                'config': 'JSON'
            },
            'aggregation': {'aggregation_id': 'AGG'},
            'limitation': {'limitation_id': 'LIM'},
            'ordering': {'ordering_id': 'ORD'},
            'group_by': {'entity_type': 'ENT', 'property_id': 'P'},
            'order_by': {'entity_type': 'ENT', 'property_id': 'P'}
        }

    def _ensure_tenants_exist(self):
        """Подтягиваем определения тенантов."""
        used_ids = set()
        for table, pks in self.context.items():
            if table in ['namespaces', 'tenants', 'clients']: continue
            for pk in pks:
                if len(pk) >= 2 and pk[1]: # pk[1] is tenant_id
                    used_ids.add(pk[1])
        
        if 'tenants' not in self.context:
            self.context['tenants'] = set()
            
        # Добавляем пустой/дефолтный тенант, если он есть в базе
        used_ids.add('') 
            
        for tid in used_ids:
            pk = (tid,)
            if pk in self.loader.db.get('tenants', {}):
                self.context['tenants'].add(pk)

    def generate_sql(self) -> str:
        lines = []
        lines.append("SET SEARCH_PATH to qe_config;\n")
        
        self._ensure_tenants_exist()
        
        # Порядок вставки важен для целостности ссылок
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
            
            # Определяем колонки
            cols = self.loader.table_cols.get(table, [])
            if not cols and pks:
                first = next(iter(pks))
                cols = list(self.loader.db[table][first].keys())
                
            # Получаем правила маппинга для текущей таблицы
            table_map = self.field_mapping.get(table, {})

            sorted_pks = sorted(list(pks))
            values_rows = []
            
            for pk in sorted_pks:
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
                            # Парсим JSON -> Маскируем -> Собираем обратно
                            try:
                                if isinstance(val, str):
                                    json_obj = json.loads(val)
                                    masked_obj = self.masker.mask_json(json_obj)
                                    val_to_write = json.dumps(masked_obj, ensure_ascii=False)
                                elif isinstance(val, (dict, list)):
                                    masked_obj = self.masker.mask_json(val)
                                    val_to_write = json.dumps(masked_obj, ensure_ascii=False)
                            except:
                                # Если не парсится, считаем текстом
                                val_to_write = self.masker.mask_text(str(val))
                                
                        elif action == 'FORMULA':
                            if isinstance(val, str):
                                val_to_write = self.masker.mask_formula(val)
                                
                        elif action == 'ARRAY_PATH':
                            # Специфично для параметров: массив путей
                            arr = self._parse_array(val)
                            masked_arr = [self.masker.register(x, 'PATH') for x in arr]
                            val_to_write = masked_arr # _format_val обработает список
                            
                        elif action and action not in ['JSON', 'FORMULA', 'ARRAY_PATH']:
                            # Прямая замена по категории (ENT, TBL, P...)
                            if isinstance(val, str) and val:
                                val_to_write = self.masker.register(val, action)
                                
                    # --- КОНЕЦ МАСКИРОВАНИЯ ---

                    vals.append(self._format_val(val_to_write))
                
                # Форматирование вывода
                complex_tables = ['entity_properties', 'vertex_functions', 'limitation']
                if table in complex_tables:
                    row_str = self._format_row_pretty(vals)
                else:
                    row_str = f"({', '.join(vals)})"
                
                values_rows.append(row_str)
            
            if values_rows:
                header = f"INSERT INTO {table} ({', '.join(cols)}) VALUES"
                body = ",\n".join(values_rows)
                lines.append(f"{header}\n{body};")
            
            lines.append("")
            
        return "\n".join(lines)

    def _parse_array(self, val) -> List[str]:
        """Парсит строковое представление массива SQL."""
        if isinstance(val, list): return [str(x) for x in val if x]
        if not isinstance(val, str): return []
        val = val.strip()
        if val.startswith('{') and val.endswith('}'):
            content = val[1:-1]
            if not content: return []
            # Простой сплит по запятой (для сложных случаев нужен csv reader, но пока так)
            parts = content.split(',')
            res = []
            for p in parts:
                p = p.strip()
                # Удаляем кавычки если есть
                if len(p) >= 2 and (p[0] in '"\'' and p[-1] in '"\''):
                    p = p[1:-1]
                if p: res.append(p)
            return res
        return []

    def _format_val(self, val: Any) -> str:
        if val is None: return "null"
        if isinstance(val, bool): return "true" if val else "false"
        if isinstance(val, (int, float)): return str(val)
        if isinstance(val, list):
            safe_list = [str(x) for x in val if x is not None]
            # Формируем SQL массив: {'val1', 'val2'}
            formatted_list = []
            for x in safe_list:
                # Экранируем одинарные кавычки для SQL
                escaped = x.replace("'", "''") 
                formatted_list.append(f"'{escaped}'" if not x.startswith("'") else x) # если уже в кавычках (от маскера), не трогаем? 
                # Нет, маскер возвращает просто строку маски. Надо кавычить.
            # Но подождите, маскер формул возвращает строку с кавычками.
            # Здесь список строк (PATH). Они "чистые".
            return "'{" + ", ".join([f'"{x}"' for x in safe_list]) + "}'" 
            
        if isinstance(val, dict):
            json_str = json.dumps(val, ensure_ascii=False)
            escaped = json_str.replace("'", "''")
            return f"'{escaped}'"
            
        if isinstance(val, str):
            # Проверка, не является ли это уже SQL выражением (например, от mask_formula)
            # mask_formula возвращает строку, которая МОЖЕТ содержать кавычки, переносы строк и т.д.
            # НО generate_sql ожидает здесь raw value, которое нужно обернуть в кавычки SQL.
            
            # ВАЖНО: Если mask_formula вернула что-то сложное, мы все равно должны вставить это как строку в INSERT.
            # Поэтому экранируем кавычки.
            escaped = val.replace("'", "''")
            return f"'{escaped}'"
            
        return f"'{str(val)}'"

    def _format_row_pretty(self, vals: List[str]) -> str:
        # Улучшенное форматирование для читаемости
        lines = []
        current_line = "  "
        VERTICAL_START = 5
        
        for i, val in enumerate(vals):
            is_last = (i == len(vals) - 1)
            suffix = "" if is_last else ", "
            
            # Если значение содержит переводы строк (функции), форматируем блоком
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
                current_line = "" # Сброс, чтобы следующая итерация добавила отступ
                continue

            # Компактная запись для первых полей
            if len(current_line) + len(val) > 120:
                 lines.append(current_line.rstrip())
                 current_line = f"  {val}{suffix}"
            else:
                 current_line += f"{val}{suffix}"
        
        if current_line.strip():
            lines.append(current_line.rstrip())
            
        return "(\n" + "\n".join(lines) + "\n)"