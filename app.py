import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import List, Dict

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка страницы
st.set_page_config(
    page_title="Prompt Builder",
    page_icon="images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Инициализация session_state (ВАЖНО: только один раз) ---
def init_session_state():
    """Централизованная инициализация session_state"""
    defaults = {
        'system_prompt': "",
        'user_query': "",
        'final_prompt': "",
        'token_count': 0,
        'selected_namespace': "",
        'prompt_versions': {},  # {version_name: {prompt: str, created: str, modified: str}}
        'current_version': None,  # Название текущей активной версии
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Функции для работы с версиями ---

def save_version(version_name: str, prompt_text: str):
    """Сохраняет новую версию промпта"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if version_name in st.session_state.prompt_versions:
        # Обновляем существующую версию
        st.session_state.prompt_versions[version_name]['prompt'] = prompt_text
        st.session_state.prompt_versions[version_name]['modified'] = now
    else:
        # Создаем новую версию
        st.session_state.prompt_versions[version_name] = {
            'prompt': prompt_text,
            'created': now,
            'modified': now
        }
    
    st.session_state.current_version = version_name

def load_version(version_name: str):
    """Загружает версию промпта"""
    if version_name in st.session_state.prompt_versions:
        st.session_state.system_prompt = st.session_state.prompt_versions[version_name]['prompt']
        # ВАЖНО: обновляем также состояние виджета text_area
        st.session_state.system_prompt_input = st.session_state.prompt_versions[version_name]['prompt']
        st.session_state.current_version = version_name

def delete_version(version_name: str):
    """Удаляет версию промпта"""
    if version_name in st.session_state.prompt_versions:
        del st.session_state.prompt_versions[version_name]
        if st.session_state.current_version == version_name:
            st.session_state.current_version = None

def export_versions() -> str:
    """Экспортирует все версии в JSON"""
    return json.dumps(st.session_state.prompt_versions, indent=2, ensure_ascii=False)

def import_versions(json_data: str):
    """Импортирует версии из JSON"""
    try:
        imported = json.loads(json_data)
        st.session_state.prompt_versions.update(imported)
        return True, f"Импортировано {len(imported)} версий"
    except Exception as e:
        return False, f"Ошибка импорта: {str(e)}"

# --- Кэшированные функции для бэкенда ---

@st.cache_resource
def get_db_manager():
    """Инициализация менеджера базы данных с кэшированием"""
    class MockDBManager:
        def get_all_namespaces(self) -> List[str]:
            return ["AN", "INS", "DEMO"]
        
        def fetch_all_data_by_namespace(self, namespace: str) -> List[dict]:
            return [{"id": 1, "content": f"Sample data from {namespace}"}]
    
    return MockDBManager()

@st.cache_resource
def get_vector_store_manager():
    """Инициализация менеджера векторного хранилища с кэшированием"""
    class MockVectorStoreManager:
        def rebuild_database(self, data: List[dict], namespace: str):
            return f"Database rebuilt for {namespace} with {len(data)} items"
        
        def search_similar(self, query: str, namespace: str, limit: int = 5) -> List[dict]:
            return [{"content": f"Similar result for: {query}", "score": 0.95}]
    
    return MockVectorStoreManager()

@st.cache_data
def load_namespaces() -> List[str]:
    """Загрузка списка namespace с кэшированием"""
    db_manager = get_db_manager()
    return db_manager.get_all_namespaces()

# --- Вспомогательные функции ---

def count_tokens(text: str) -> int:
    """Подсчет токенов в тексте (упрощенная версия)"""
    return int(len(text.split()) * 1.3)

def generate_final_prompt(system_prompt: str, user_query: str, namespace: str) -> str:
    """Генерация финального промпта"""
    vector_manager = get_vector_store_manager()
    similar_results = vector_manager.search_similar(user_query, namespace)
    
    context_parts = []
    for result in similar_results:
        context_parts.append(f"- {result['content']}")
    
    context = "\n".join(context_parts) if context_parts else "Нет релевантного контекста"
    
    return f"""-- Системный промпт:
{system_prompt}

-- Контекст из векторной БД (namespace: {namespace}):
{context}

-- SQL запрос:
-- TODO: Интегрировать с core_logic.generate_sql_inserts()
SELECT * FROM data WHERE query LIKE '%{user_query}%';

-- Пользовательский запрос:
{user_query}"""

# --- Коллбэки для кнопок ---

def clear_system_prompt():
    """Очищает системный промпт."""
    st.session_state.system_prompt = ""
    if 'system_prompt_input' in st.session_state:
        st.session_state.system_prompt_input = ""
    
def clear_user_query():
    """Очищает запрос пользователя."""
    st.session_state.user_query = ""
    if 'user_query_input' in st.session_state:
        st.session_state.user_query_input = ""

def clear_final_prompt():
    """Очищает готовый промпт и счетчик токенов."""
    st.session_state.final_prompt = ""
    st.session_state.token_count = 0

# --- Основной интерфейс ---

# Заголовок приложения
st.title("🔨 Prompt Builder")

# Верхняя панель управления
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if 'show_system_prompt' not in st.session_state:
            st.session_state.show_system_prompt = True
            
        st.toggle(
            "Показать системный промпт",
            key="show_system_prompt"
        )
    
    with col2:
        namespaces = load_namespaces()
        if namespaces:
            if st.session_state.selected_namespace not in namespaces:
                st.session_state.selected_namespace = namespaces[0]
            
            selected = st.selectbox(
                "Выберите namespace",
                options=namespaces,
                index=namespaces.index(st.session_state.selected_namespace),
                key="namespace_selector"
            )
            st.session_state.selected_namespace = selected
        else:
            st.warning("⚠️ Нет доступных namespace")
    
    with col3:
        if st.button("🔄 Обновить векторную БД", use_container_width=True):
            with st.spinner('Обновление базы...'):
                try:
                    db_manager = get_db_manager()
                    vector_manager = get_vector_store_manager()
                    
                    data = db_manager.fetch_all_data_by_namespace(st.session_state.selected_namespace)
                    result = vector_manager.rebuild_database(data, st.session_state.selected_namespace)
                    
                    st.success(f"✅ Векторная база успешно обновлена! {result}")
                except Exception as e:
                    st.error(f"❌ Ошибка при обновлении: {str(e)}")

st.markdown("---")

# Системный промпт с версионированием (условно отображаемый)
if st.session_state.show_system_prompt:
    # Панель управления версиями
    with st.expander("📚 Управление версиями системного промпта", expanded=True):
        tab1, tab2 = st.tabs(["💾 Сохранить", "📂 Загрузить"])
        
        # Вкладка сохранения
        with tab1:
            col_save_name, col_save_btn = st.columns([3, 1])
            with col_save_name:
                save_name = st.text_input(
                    "Название версии",
                    placeholder="Например: Версия для SQL генерации",
                    key="save_version_name"
                )
            with col_save_btn:
                st.write("")  # Отступ для выравнивания
                st.write("")
                if st.button("💾 Сохранить", use_container_width=True):
                    if save_name.strip():
                        save_version(save_name.strip(), st.session_state.system_prompt)
                        st.success(f"✅ Версия '{save_name}' сохранена!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Введите название версии")
        
        # Вкладка загрузки
        with tab2:
            if st.session_state.prompt_versions:
                for version_name, version_data in st.session_state.prompt_versions.items():
                    with st.container():
                        col_info, col_actions = st.columns([3, 1])
                        
                        with col_info:
                            is_current = version_name == st.session_state.current_version
                            status = "🟢 Активна" if is_current else ""
                            
                            st.markdown(f"**{version_name}** {status}")
                            st.caption(f"Создана: {version_data['created']} | "
                                     f"Изменена: {version_data['modified']}")
                            
                            # Сворачиваемый текст промпта
                            with st.expander("👁️ Показать текст промпта", expanded=False):
                                st.text_area(
                                    "Текст промпта",
                                    value=version_data['prompt'],
                                    height=200,
                                    disabled=True,
                                    key=f"preview_{version_name}",
                                    label_visibility="collapsed"
                                )
                        
                        with col_actions:
                            col_load, col_del = st.columns(2)
                            with col_load:
                                if st.button("📥", key=f"load_{version_name}", 
                                           help="Загрузить эту версию"):
                                    load_version(version_name)
                                    st.success(f"✅ Загружена версия '{version_name}'")
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️", key=f"delete_{version_name}",
                                           help="Удалить эту версию"):
                                    delete_version(version_name)
                                    st.success(f"✅ Версия '{version_name}' удалена")
                                    st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("📭 Нет сохраненных версий. Создайте первую версию во вкладке 'Сохранить'")
    
    # Текстовое поле системного промпта
    def update_system_prompt():
        st.session_state.system_prompt = st.session_state.system_prompt_input
    
    # Показываем название активной версии
    version_label = f"📝 Системный промпт"
    if st.session_state.current_version:
        version_label += f" (🟢 {st.session_state.current_version})"
    
    st.text_area(
        version_label,
        value=st.session_state.system_prompt,
        height=150,
        placeholder="Введите системный промпт здесь...",
        key='system_prompt_input',
        on_change=update_system_prompt,
        help="Системный промпт будет добавлен в начало финального промпта"
    )
    
    # Кнопки управления системным промптом
    col_clear, col_copy = st.columns(2)
    with col_clear:
        st.button("🗑️ Очистить", on_click=clear_system_prompt, key="clear_sys")
    with col_copy:
        if st.session_state.system_prompt:
            if st.button("📋 Копировать", key="copy_sys"):
                st.write(f'<textarea id="sys_copy" style="position:absolute;left:-9999px">{st.session_state.system_prompt}</textarea>', unsafe_allow_html=True)
                st.write('<script>document.getElementById("sys_copy").select();document.execCommand("copy");</script>', unsafe_allow_html=True)
                st.toast("✅ Скопировано!")
        else:
            st.button("📋 Копировать", key="copy_sys", disabled=True)
    
    st.markdown("---")

# Основной контент - две колонки
col_left, col_right = st.columns(2)

# Левая колонка - "Мой запрос"
with col_left:
    st.subheader("💬 Мой запрос")
    
    def update_user_query():
        st.session_state.user_query = st.session_state.user_query_input
    
    st.text_area(
        "Введите ваш запрос",
        value=st.session_state.user_query,
        height=400,
        placeholder="Введите ваш запрос здесь...",
        key='user_query_input',
        on_change=update_user_query,
        label_visibility="collapsed"
    )
    
    # Кнопки управления пользовательским запросом
    col_clear_user, col_copy_user = st.columns(2)
    with col_clear_user:
        st.button("🗑️ Очистить запрос", on_click=clear_user_query, key="clear_user")
    with col_copy_user:
        if st.session_state.user_query:
            if st.button("📋 Копировать запрос", key="copy_user"):
                st.write(f'<textarea id="user_copy" style="position:absolute;left:-9999px">{st.session_state.user_query}</textarea>', unsafe_allow_html=True)
                st.write('<script>document.getElementById("user_copy").select();document.execCommand("copy");</script>', unsafe_allow_html=True)
                st.toast("✅ Скопировано!")
        else:
            st.button("📋 Копировать запрос", key="copy_user", disabled=True)

# Правая колонка - "Готовый промпт"
with col_right:
    st.subheader("✨ Готовый промпт")
    
    if st.session_state.final_prompt:
        st.code(st.session_state.final_prompt, language="sql", line_numbers=True)
    else:
        st.info("👈 Введите запрос и нажмите 'Сгенерировать'")
    
    # Кнопки управления готовым промптом
    col_clear_final, col_copy_final = st.columns(2)
    with col_clear_final:
        st.button("🗑️ Очистить промпт", on_click=clear_final_prompt, key="clear_final")
    with col_copy_final:
        if st.session_state.final_prompt:
            if st.button("📋 Копировать промпт", key="copy_final"):
                st.write(f'<textarea id="final_copy" style="position:absolute;left:-9999px">{st.session_state.final_prompt}</textarea>', unsafe_allow_html=True)
                st.write('<script>document.getElementById("final_copy").select();document.execCommand("copy");</script>', unsafe_allow_html=True)
                st.toast("✅ Скопировано!")
        else:
            st.button("📋 Копировать промпт", key="copy_final", disabled=True)
    
    # Счетчик токенов с визуализацией
    token_count = st.session_state.token_count
    max_tokens = 128000
    progress = min(token_count / max_tokens, 1.0)
    
    col_tokens, col_bar = st.columns([1, 3])
    with col_tokens:
        st.caption(f"**Токены:** {token_count:,} / {max_tokens:,}")
    with col_bar:
        st.progress(progress)

# Нижняя панель - кнопка генерации
st.markdown("---")

col_gen, col_info = st.columns([3, 1])
with col_gen:
    if st.button("🚀 Сгенерировать промпт", type="primary", use_container_width=True):
        if not st.session_state.user_query.strip():
            st.error("❌ Пожалуйста, введите запрос в поле 'Мой запрос'")
        else:
            with st.spinner("⏳ Генерация контекста..."):
                try:
                    st.session_state.final_prompt = generate_final_prompt(
                        st.session_state.system_prompt,
                        st.session_state.user_query,
                        st.session_state.selected_namespace
                    )
                    
                    st.session_state.token_count = count_tokens(st.session_state.final_prompt)
                    
                    st.success("✅ Промпт успешно сгенерирован!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка при генерации промпта: {str(e)}")

with col_info:
    with st.popover("ℹ️ Справка"):
        st.markdown("""
        **Как использовать:**
        1. Выберите namespace
        2. Создайте или загрузите версию системного промпта
        3. Введите запрос
        4. Нажмите "Сгенерировать"
        
        **Версионирование:**
        - Сохраняйте разные варианты промптов
        - Быстро переключайтесь между версиями
        - Экспортируйте/импортируйте версии
        """)

# Информация в сайдбаре
st.sidebar.markdown("### 📊 О приложении")
st.sidebar.info("""
**Prompt Builder v2.0**

Приложение для построения промптов с:
- Версионированием системных промптов
- Векторной базой данных
- Контекстным поиском
- Автоматической генерацией SQL
""")

st.sidebar.markdown("### 📈 Статистика")
st.sidebar.metric("Сохраненных версий", len(st.session_state.prompt_versions))
st.sidebar.metric("Длина системного промпта", f"{len(st.session_state.system_prompt)} символов")
st.sidebar.metric("Длина запроса", f"{len(st.session_state.user_query)} символов")
st.sidebar.metric("Токенов в финальном промпте", st.session_state.token_count)

if st.session_state.current_version:
    st.sidebar.success(f"🟢 Активна: {st.session_state.current_version}")

if __name__ == "__main__":
    pass