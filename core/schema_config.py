from typing import Dict, List

# ==========================================
# 🔑 ПЕРВИЧНЫЕ КЛЮЧИ (PRIMARY KEYS)
# ==========================================
# Словарь, определяющий, какие поля составляют уникальный идентификатор (PK) для каждой таблицы.
# Используется в DbDataLoader для создания уникальных ключей в словаре данных.
# Формат: 'имя_таблицы': ['список', 'полей', 'ключа']
PRIMARY_KEYS: Dict[str, List[str]] = {
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

# ==========================================
# 🎭 ПРАВИЛА МАСКИРОВАНИЯ (FIELD MAPPING)
# ==========================================
# Определяет, как маскировать конкретные поля в таблицах при генерации SQL.
# Ключ: имя таблицы.
# Значение: словарь {'имя_колонки': 'ДЕЙСТВИЕ'}.
#
# Виды действий:
# - 'CATEGORY' (например, 'ENT', 'TEN', 'TBL'): Прямая замена значения на маску (person -> ENT_1).
# - 'JSON': Значение парсится как JSON, и маскирование происходит рекурсивно внутри.
# - 'FORMULA': Значение обрабатывается парсером формул (mask_formula).
# - 'ARRAY_PATH': Специфично для путей, обрабатывается как массив строк.
FIELD_MAPPING: Dict[str, Dict[str, str]] = {
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