import streamlit as st
import sys
import os

from typing import List
from clipboard_component import copy_component

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка страницы
st.set_page_config(
    page_title="Prompt Builder",
    page_icon="images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Инициализация session_state
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = ""
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""
if 'final_prompt' not in st.session_state:
    st.session_state.final_prompt = ""
if 'token_count' not in st.session_state:
    st.session_state.token_count = 0
if 'show_system_prompt' not in st.session_state:
    st.session_state.show_system_prompt = True
if 'selected_namespace' not in st.session_state:
    st.session_state.selected_namespace = ""

# --- Кэшированные функции для бэкенда ---

@st.cache_resource
def get_db_manager():
    """Инициализация менеджера базы данных с кэшированием"""
    # TODO: Заменить на реальную инициализацию
    class MockDBManager:
        def get_all_namespaces(self) -> List[str]:
            return ["AN", "INS", "DEMO"]
        
        def fetch_all_data_by_namespace(self, namespace: str) -> List[dict]:
            return [{"id": 1, "content": f"Sample data from {namespace}"}]
    
    return MockDBManager()

@st.cache_resource
def get_vector_store_manager():
    """Инициализация менеджера векторного хранилища с кэшированием"""
    # TODO: Заменить на реальную инициализацию
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
    return len(text.split())

def generate_final_prompt(system_prompt: str, user_query: str, namespace: str) -> str:
    """Генерация финального промпта"""
    # TODO: Интегрировать с core_logic
    vector_manager = get_vector_store_manager()
    similar_results = vector_manager.search_similar(user_query, namespace)
    
    context_parts = []
    for result in similar_results:
        context_parts.append(f"- {result['content']}")
    
    context = "\n".join(context_parts) if context_parts else "Нет релевантного контекста"
    
    return f"""-- Системный промпт:
{system_prompt}

-- Контекст из векторной БД:
{context}

-- SQL запрос:
-- TODO: Интегрировать с core_logic.generate_sql_inserts()
SELECT * FROM data WHERE query LIKE '%{user_query}%';

-- Пользовательский запрос:
{user_query}"""

# --- Основной интерфейс ---

# Заголовок приложения
st.title("Prompt Builder")

# Верхняя панель управления
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Кнопка скрытия/показа системного промпта
        if st.toggle("Показать системный промпт", value=st.session_state.show_system_prompt):
            st.session_state.show_system_prompt = True
        else:
            st.session_state.show_system_prompt = False
    
    with col2:
        # Выпадающий список namespace
        namespaces = load_namespaces()
        if namespaces:
            if st.session_state.selected_namespace not in namespaces:
                st.session_state.selected_namespace = namespaces[0]
            
            st.session_state.selected_namespace = st.selectbox(
                "Выберите namespace",
                options=namespaces,
                index=namespaces.index(st.session_state.selected_namespace)
            )
        else:
            st.warning("Нет доступных namespace")
    
    with col3:
        # Кнопка обновления векторной БД
        if st.button("Обновить векторную БД"):
            with st.spinner('Обновление базы...'):
                try:
                    db_manager = get_db_manager()
                    vector_manager = get_vector_store_manager()
                    
                    # Получаем данные для выбранного namespace
                    data = db_manager.fetch_all_data_by_namespace(st.session_state.selected_namespace)
                    
                    # Перестраиваем векторную базу
                    result = vector_manager.rebuild_database(data, st.session_state.selected_namespace)
                    
                    st.success(f"Векторная база успешно обновлена! {result}")
                except Exception as e:
                    st.error(f"Произошла ошибка при обновлении: {str(e)}")

# Системный промпт (условно отображаемый)
if st.session_state.show_system_prompt:
    st.session_state.system_prompt = st.text_area(
        "Системный промпт",
        value=st.session_state.system_prompt,
        height=150,
        placeholder="Это поле для системного промпта..."
    )
    
    # Кнопки управления системным промптом
    col_clear, col_copy = st.columns(2)
    with col_clear:
        if st.button("Очистить системный промпт"):
            st.session_state.system_prompt = ""
    with col_copy:
        if st.button("Копировать системный промпт"):
            copy_component(content=st.session_state.system_prompt, name="system_prompt")
            st.info("Текст скопирован в буфер обмена!")

# Основной контент - две колонки
col_left, col_right = st.columns(2)

# Левая колонка - "Мой запрос"
with col_left:
    st.subheader("Мой запрос")
    st.session_state.user_query = st.text_area(
        "Введите ваш запрос",
        value=st.session_state.user_query,
        height=400,
        placeholder="Введите ваш запрос здесь..."
    )
    
    # Кнопки управления пользовательским запросом
    col_clear_user, col_copy_user = st.columns(2)
    with col_clear_user:
        if st.button("Очистить мой запрос"):
            st.session_state.user_query = ""
    with col_copy_user:
        if st.button("Копировать мой запрос"):
            copy_component(content=st.session_state.user_query, name="user_query")
            st.info("Текст скопирован в буфер обмена!")

# Правая колонка - "Готовый промпт"
with col_right:
    st.subheader("Готовый промпт")
    
    # Отображение готового промпта как кода
    if st.session_state.final_prompt:
        st.code(st.session_state.final_prompt, language="sql", line_numbers=True)
    else:
        st.info("Здесь будет отображаться сгенерированный промпт")
    
    # Кнопки управления готовым промптом
    col_clear_final, col_copy_final = st.columns(2)
    with col_clear_final:
        if st.button("Очистить готовый промпт"):
            st.session_state.final_prompt = ""
            st.session_state.token_count = 0
    with col_copy_final:
        if st.button("Копировать готовый промпт"):
            if st.session_state.final_prompt:
                copy_component(content=st.session_state.final_prompt, name="final_prompt")
                st.info("Текст скопирован в буфер обмена!")
            else:
                st.warning("Нет текста для копирования")
    
    # Счетчик токенов
    st.caption(f"Токены: {st.session_state.token_count} / 128000")

# Нижняя панель - кнопка генерации
st.markdown("---")
if st.button("Сгенерировать", type="primary", use_container_width=True):
    if not st.session_state.user_query.strip():
        st.error("Пожалуйста, введите запрос в поле 'Мой запрос'")
    else:
        with st.spinner("Генерация контекста..."):
            try:
                # Генерация финального промпта
                st.session_state.final_prompt = generate_final_prompt(
                    st.session_state.system_prompt,
                    st.session_state.user_query,
                    st.session_state.selected_namespace
                )
                
                # Подсчет токенов
                st.session_state.token_count = count_tokens(st.session_state.final_prompt)
                
                st.success("Промпт успешно сгенерирован!")
            except Exception as e:
                st.error(f"Ошибка при генерации промпта: {str(e)}")

# Информация о приложении
st.sidebar.markdown("### О приложении")
st.sidebar.info("Это приложение для построения промптов с использованием векторной базы данных.")

if __name__ == "__main__":
    # Для локального запуска через streamlit run app.py
    pass