import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
import streamlit.components.v1 as components

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка страницы
st.set_page_config(
    page_title="Prompt Builder",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Константы ---
VERSIONS_FILE = Path("prompt_versions.json")

# --- ЗАГЛУШКИ для функций маскирования (заменишь на свою логику) ---

def mask_text(text: str) -> Tuple[str, Dict[str, str]]:
    """
    ЗАГЛУШКА: Маскирует конфиденциальные данные в тексте
    
    Замени эту функцию на свою логику маскирования!
    
    Args:
        text: Исходный текст для маскирования
        
    Returns:
        Tuple[str, Dict[str, str]]: (замаскированный_текст, словарь_замен)
        где словарь_замен = {маска: оригинальное_значение}
    """
    # TODO: Интегрировать твою логику маскирования
    masked_text = text
    mapping = {}
    
    # Пример заглушки (удали это когда добавишь свою логику):
    # mapping = {
    #     "MASK_001": "original_value_1",
    #     "MASK_002": "original_value_2"
    # }
    
    return masked_text, mapping

def unmask_text(text: str, mapping: Dict[str, str]) -> str:
    """
    ЗАГЛУШКА: Восстанавливает оригинальные данные из замаскированного текста
    
    Замени эту функцию на свою логику расшифровки!
    
    Args:
        text: Замаскированный текст
        mapping: Словарь замен {маска: оригинальное_значение}
        
    Returns:
        str: Расшифрованный текст
    """
    # TODO: Интегрировать твою логику расшифровки
    unmasked_text = text
    
    # Пример заглушки (удали это когда добавишь свою логику):
    for mask, original in mapping.items():
        unmasked_text = unmasked_text.replace(mask, original)
    
    return unmasked_text

# --- Функции для работы с файлами ---

def load_versions_from_file() -> Dict:
    """Загружает версии промптов из файла"""
    if VERSIONS_FILE.exists():
        try:
            with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Проверяем, что файл не пустой
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            st.error(f"❌ Ошибка формата файла версий: {str(e)}")
            st.warning("💡 Попробуйте удалить файл prompt_versions.json и начать заново")
            return {}
        except Exception as e:
            st.error(f"❌ Ошибка загрузки версий: {str(e)}")
            return {}
    return {}

def save_versions_to_file(versions: Dict):
    """Сохраняет версии промптов в файл"""
    try:
        with open(VERSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(versions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"❌ Ошибка сохранения версий: {str(e)}")

# --- Инициализация session_state ---
def init_session_state():
    """Централизованная инициализация session_state"""
    defaults = {
        'system_prompt': "",
        'user_query': "",
        'final_prompt': "",
        'masked_prompt': "",
        'masking_dictionary': {},
        'llm_response': "",
        'unmasked_response': "",
        'token_count': 0,
        'selected_namespace': "",
        'prompt_versions': load_versions_from_file(),
        'current_version': None,
        'show_step1': False,
        'show_step2': True,
        'show_step3': False,
        'enable_masking': True,
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
        st.session_state.prompt_versions[version_name]['prompt'] = prompt_text
        st.session_state.prompt_versions[version_name]['modified'] = now
    else:
        st.session_state.prompt_versions[version_name] = {
            'prompt': prompt_text,
            'created': now,
            'modified': now
        }
    
    st.session_state.current_version = version_name
    save_versions_to_file(st.session_state.prompt_versions)

def load_version(version_name: str):
    """Загружает версию промпта"""
    if version_name in st.session_state.prompt_versions:
        st.session_state.system_prompt = st.session_state.prompt_versions[version_name]['prompt']
        st.session_state.current_version = version_name

def delete_version(version_name: str):
    """Удаляет версию промпта"""
    if version_name in st.session_state.prompt_versions:
        del st.session_state.prompt_versions[version_name]
        if st.session_state.current_version == version_name:
            st.session_state.current_version = None
        save_versions_to_file(st.session_state.prompt_versions)

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

# --- Функция для копирования в буфер ---
def copy_to_clipboard(text: str, button_key: str):
    """Универсальная функция для копирования текста в буфер обмена"""
    st.write(f'<textarea id="{button_key}" style="position: absolute; left: -9999px;">{text}</textarea>', unsafe_allow_html=True)
    components.html(f"""
        <script>
            var copyText = window.parent.document.getElementById("{button_key}");
            if (copyText) {{
                copyText.select();
                window.parent.document.execCommand("copy");
            }}
        </script>
    """, height=0)

# --- CSS для улучшения визуального оформления ---
st.markdown("""
<style>
    /* === ОБЩИЙ ФОН И БАЗОВЫЕ НАСТРОЙКИ === */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8edf3 100%);
    }
    
    /* Уменьшаем отступы между колонками */
    div[data-testid="column"] {
        padding: 0 5px !important;
    }
    
    /* Все кнопки на всю ширину */
    .stButton button {
        width: 100%;
    }
    
    /* === КНОПКИ ЭТАПОВ (1️⃣, 2️⃣, 3️⃣) - Мягкий синий === */
    button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        font-size: 1.1em !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.25) !important;
        transition: all 0.3s ease !important;
        margin: 20px 0 15px 0 !important;
        letter-spacing: 0.3px;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-3px) scale(1.01);
    }
    
    /* === КНОПКИ ДЕЙСТВИЙ (🚀 Сгенерировать, 🔓 Расшифровать) - Коралловый === */
    .stColumn button[kind="primary"],
    .stColumn .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        margin: 0 !important;
        padding: 0.6rem 1.2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        box-shadow: 0 3px 12px rgba(245, 87, 108, 0.25) !important;
        letter-spacing: 0.2px;
    }
    
    .stColumn button[kind="primary"]:hover {
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%) !important;
        box-shadow: 0 5px 18px rgba(245, 87, 108, 0.4) !important;
        transform: translateY(-2px) scale(1.02) !important;
    }
    
    /* === ОБЫЧНЫЕ КНОПКИ (Очистить, Копировать и т.д.) - Нейтральные === */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%) !important;
        color: #4a5568 !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #ebedee 0%, #fdfbfb 100%) !important;
        border-color: #cbd5e0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        transform: translateY(-1px);
    }
    
    /* === ТЕКСТОВЫЕ ОБЛАСТИ === */
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* === СЕЛЕКТЫ === */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        background: white !important;
    }
    
    /* === ЧЕКБОКСЫ === */
    .stCheckbox {
        background: white;
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 500 !important;
    }
    
    /* === ПРОГРЕСС БАР === */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px !important;
    }
    
    /* === ЗАГОЛОВКИ === */
    h1, h2, h3 {
        color: #2d3748 !important;
        font-weight: 700 !important;
    }
    
    /* === МЕТРИКИ В САЙДБАРЕ === */
    [data-testid="stMetricValue"] {
        color: #667eea !important;
        font-weight: 600 !important;
    }
    
    /* === САЙДБАР === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%) !important;
    }

</style>
""", unsafe_allow_html=True)

# --- Основной интерфейс ---

# анимация заголовка!
components.html("""
<style>
    .animated-title {
        text-align: center;
        font-size: 3em;
        font-weight: 700;
        color: #2d3748;
        margin: 0;
        padding: 0;
        user-select: none;
        font-family: "Source Sans Pro", sans-serif;
    }
    
    .hammer-emoji {
        display: inline-block;
        font-size: 1.2em;
        margin-right: 15px;
        cursor: pointer;
        transform-origin: bottom right;
    }
    
    @keyframes hammer-swing {
        0% { transform: rotate(0deg); }
        15% { transform: rotate(-35deg); }
        30% { transform: rotate(25deg); }
        45% { transform: rotate(-20deg); }
        60% { transform: rotate(15deg); }
        75% { transform: rotate(-10deg); }
        90% { transform: rotate(5deg); }
        100% { transform: rotate(0deg); }
    }
    
    .hammer-animate {
        animation: hammer-swing 0.8s ease-in-out;
    }
    
    /* Градиентный текст для заголовка */
    .title-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
</style>

<div class="animated-title">
    <span class="hammer-emoji" id="hammer">🔨</span>
    <span class="title-text">Prompt Builder</span>
</div>

<script>
    document.getElementById('hammer').addEventListener('click', function() {
        this.classList.add('hammer-animate');
        setTimeout(() => {
            this.classList.remove('hammer-animate');
        }, 800);
    });
</script>
""", height=100)

# ========== ЭТАП 1: Системный промпт ==========
step1_icon = "▼" if st.session_state.show_step1 else "▶"
if st.button(
    f'1️⃣ Настройка системного промпта {step1_icon}', 
    key='step1_toggle', 
    use_container_width=True,
    type='primary'  # Делаем primary чтобы отличать от других кнопок
):
    st.session_state.show_step1 = not st.session_state.show_step1
    st.rerun()

if st.session_state.show_step1:
    # Системный промпт с версионированием
    with st.container():
        # Панель управления версиями
        with st.expander("📚 Управление версиями системного промпта", expanded=False):
            tab1, tab2 = st.tabs(["💾 Сохранить", "📂 Загрузить"])
            
            with tab1:
                col_save_name, col_save_btn = st.columns([4, 1])
                with col_save_name:
                    save_name = st.text_input(
                        "Название версии",
                        placeholder="Например: Версия для SQL генерации",
                        key="save_version_name"
                    )
                with col_save_btn:
                    st.write("")
                    st.write("")
                    if st.button("💾 Сохранить", use_container_width=True):
                        if save_name and save_name.strip():
                            save_version(save_name.strip(), st.session_state.system_prompt)
                            st.success(f"✅ Версия '{save_name}' сохранена!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Введите название версии")
            
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
                                
                                with st.expander("🔍 Показать текст промпта", expanded=False):
                                    st.text_area(
                                        "Текст промпта",
                                        value=version_data['prompt'],
                                        height=200,
                                        disabled=True,
                                        key=f"preview_{version_name}_{version_data['modified']}",
                                        label_visibility="collapsed"
                                    )
                            
                            with col_actions:
                                col_load, col_del = st.columns(2)
                                with col_load:
                                    if st.button("📥", key=f"load_{version_name}", 
                                               help="Загрузить эту версию",
                                               use_container_width=True):
                                        load_version(version_name)
                                        st.success(f"✅ Загружена версия '{version_name}'")
                                        st.rerun()
                                with col_del:
                                    if st.button("🗑️", key=f"delete_{version_name}",
                                               help="Удалить эту версию",
                                               use_container_width=True):
                                        delete_version(version_name)
                                        st.success(f"✅ Версия '{version_name}' удалена")
                                        st.rerun()
                            
                            st.markdown("---")
                else:
                    st.info("📭 Нет сохраненных версий")
        
        version_label = f"📝 Системный промпт"
        if st.session_state.current_version:
            version_label += f" (🟢 {st.session_state.current_version})"
        
        system_prompt_value = st.text_area(
            version_label,
            height=150,
            placeholder="Введите системный промпт здесь...",
            key='system_prompt',
            help="Системный промпт будет добавлен в начало финального промпта"
        )
        
        col_clear, col_copy = st.columns([1, 1])
        with col_clear:
            if st.button("🗑️ Очистить", key="clear_sys", use_container_width=True, 
                        disabled=not st.session_state.system_prompt,
                        on_click=lambda: st.session_state.update({'system_prompt': ''})):
                pass
        with col_copy:
            if st.session_state.system_prompt:
                if st.button("📋 Копировать", key="copy_sys", use_container_width=True):
                    copy_to_clipboard(st.session_state.system_prompt, "copy_sys")
                    st.toast("✅ Скопировано!")
            else:
                st.button("📋 Копировать", key="copy_sys_disabled", disabled=True, use_container_width=True)
        
        st.markdown("---")

# ========== ЭТАП 2: Генерация промпта ==========
step2_icon = "▼" if st.session_state.show_step2 else "▶"
if st.button(
    f'2️⃣ Генерация промпта с контекстом {step2_icon}', 
    key='step2_toggle', 
    use_container_width=True,
    type='primary'  # Делаем primary
):
    st.session_state.show_step2 = not st.session_state.show_step2
    st.rerun()

if st.session_state.show_step2:
    # Выбор namespace и маскирование в одной строке
    with st.container():
        col_namespace, col_masking = st.columns([2, 1])
        
        with col_namespace:
            namespaces = load_namespaces()
            if namespaces:
                if st.session_state.selected_namespace not in namespaces:
                    st.session_state.selected_namespace = namespaces[0]
                
                selected = st.selectbox(
                    "📂 Выберите namespace",
                    options=namespaces,
                    index=namespaces.index(st.session_state.selected_namespace),
                    key="namespace_selector"
                )
                st.session_state.selected_namespace = selected
            else:
                st.warning("⚠️ Нет доступных namespace")
        
        with col_masking:
            st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
            masking_enabled = st.checkbox(
                "🎭 Включить маскирование",
                value=st.session_state.enable_masking,
                key="enable_masking_checkbox",
                help="Автоматически маскирует конфиденциальные данные в промпте"
            )
            st.session_state.enable_masking = masking_enabled

    st.markdown("---")

    # Основной контент - две колонки
    col_left, col_right = st.columns(2)

    # Левая колонка - "Мой запрос"
    with col_left:
        st.subheader("💬 Мой запрос")
        
        user_query_value = st.text_area(
            "Введите ваш запрос",
            height=400,
            placeholder="Введите ваш запрос здесь...",
            key='user_query',
            label_visibility="collapsed"
        )
        
        col_clear_user, col_copy_user = st.columns([1, 1])
        with col_clear_user:
            if st.button("🗑️ Очистить запрос", key="clear_user", use_container_width=True,
                        disabled=not st.session_state.user_query,
                        on_click=lambda: st.session_state.update({'user_query': ''})):
                pass
        with col_copy_user:
            if st.session_state.user_query:
                if st.button("📋 Копировать запрос", key="copy_user", use_container_width=True):
                    copy_to_clipboard(st.session_state.user_query, "copy_user")
                    st.toast("✅ Скопировано!")
            else:
                st.button("📋 Копировать запрос", key="copy_user_disabled", disabled=True, use_container_width=True)

    # Правая колонка - "Готовый промпт"
    with col_right:
        st.subheader("✨ Готовый промпт")
        
        # Табы для оригинального и замаскированного промпта
        if st.session_state.final_prompt:
            if st.session_state.enable_masking and st.session_state.masked_prompt:
                tab_masked, tab_original = st.tabs(["🎭 Замаскированный (отправить в LLM)", "👁️ Оригинальный"])
                
                with tab_masked:
                    st.code(st.session_state.masked_prompt, language="sql", line_numbers=True)
                    
                    # Показываем статистику маскирования
                    if st.session_state.masking_dictionary:
                        with st.expander("🔍 Словарь замен", expanded=False):
                            for mask, original in st.session_state.masking_dictionary.items():
                                st.text(f"{mask} → {original}")
                
                with tab_original:
                    st.code(st.session_state.final_prompt, language="sql", line_numbers=True)
            else:
                st.code(st.session_state.final_prompt, language="sql", line_numbers=True)
        else:
            st.info("👈 Введите запрос и нажмите 'Сгенерировать'")
        
        col_clear_final, col_copy_final = st.columns([1, 1])
        with col_clear_final:
            if st.button("🗑️ Очистить промпт", key="clear_final", use_container_width=True,
                        disabled=not st.session_state.final_prompt,
                        on_click=lambda: st.session_state.update({
                            'final_prompt': '', 
                            'masked_prompt': '', 
                            'token_count': 0
                        })):
                pass
        with col_copy_final:
            prompt_to_copy = st.session_state.masked_prompt if (st.session_state.enable_masking and st.session_state.masked_prompt) else st.session_state.final_prompt
            if prompt_to_copy:
                if st.button("📋 Копировать промпт", key="copy_final", use_container_width=True):
                    copy_to_clipboard(prompt_to_copy, "copy_final")
                    st.toast("✅ Скопировано!")
            else:
                st.button("📋 Копировать промпт", key="copy_final_disabled", disabled=True, use_container_width=True)
        
        # Счетчик токенов
        token_count = st.session_state.token_count
        max_tokens = 128000
        progress = min(token_count / max_tokens, 1.0)
        
        col_tokens, col_bar = st.columns([1, 3])
        with col_tokens:
            st.caption(f"**Токены:** {token_count:,} / {max_tokens:,}")
        with col_bar:
            st.progress(progress)

    st.markdown("---")

    # Нижняя панель - кнопки генерации
    col_refresh, col_gen, col_info = st.columns([1, 2, 1])

    with col_refresh:
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

    with col_gen:
        if st.button("🚀 Сгенерировать промпт", type="primary", use_container_width=True):
            # <-- ИСПРАВЛЕНИЕ 2: Добавлена проверка на None перед .strip()
            if not (st.session_state.user_query or "").strip():
                st.error("❌ Пожалуйста, введите запрос")
            else:
                with st.spinner("⏳ Генерация промпта..."):
                    try:
                        # Генерируем оригинальный промпт
                        # <-- ИСПРАВЛЕНИЕ 3 и 4: Гарантируем передачу str в функцию
                        st.session_state.final_prompt = generate_final_prompt(
                            st.session_state.system_prompt or "",
                            st.session_state.user_query or "",
                            st.session_state.selected_namespace
                        )
                        
                        # Маскируем при необходимости
                        if st.session_state.enable_masking:
                            # TODO: Здесь вызывается твоя функция маскирования
                            masked, mapping = mask_text(st.session_state.final_prompt)
                            st.session_state.masked_prompt = masked
                            st.session_state.masking_dictionary = mapping
                            
                            st.session_state.token_count = count_tokens(masked)
                            
                            if mapping:
                                st.success(f"✅ Промпт сгенерирован! Замаскировано {len(mapping)} элементов")
                            else:
                                st.info("ℹ️ Конфиденциальные данные не обнаружены")
                        else:
                            st.session_state.masked_prompt = ""
                            st.session_state.masking_dictionary = {}
                            st.session_state.token_count = count_tokens(st.session_state.final_prompt)
                            st.success("✅ Промпт успешно сгенерирован!")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка при генерации промпта: {str(e)}")

    with col_info:
        with st.popover("ℹ️ Справка"):
            st.markdown("""
            **Как использовать:**
            
            **Этап 1: Системный промпт**
            - Создайте или загрузите версию системного промпта
            
            **Этап 2: Генерация промпта**
            - Выберите namespace
            - Включите маскирование (если нужно)
            - Введите свой запрос
            - При необходимости обновите векторную БД
            - Нажмите "Сгенерировать промпт"
            - Скопируйте замаскированный промпт и отправьте в LLM
            
            **Этап 3: Расшифровка ответа**
            - Вставьте ответ от LLM
            - Нажмите "Расшифровать"
            - Получите ответ с реальными данными
            
            **TODO для интеграции:**
            - Замените функцию `mask_text()` на свою логику маскирования
            - Замените функцию `unmask_text()` на свою логику расшифровки
            """)

# ========== ЭТАП 3: Расшифровка ответа LLM ==========
step3_icon = "▼" if st.session_state.show_step3 else "▶"
if st.button(
    f'3️⃣ Расшифровка ответа LLM {step3_icon}', 
    key='step3_toggle', 
    use_container_width=True,
    type='primary'  # Делаем primary
):
    st.session_state.show_step3 = not st.session_state.show_step3
    st.rerun()

if st.session_state.show_step3:
    # Блок для расшифровки ответа LLM
    col_llm_left, col_llm_right = st.columns(2)

    with col_llm_left:
        st.markdown("**Ответ LLM (замаскированный)**")
        
        llm_response_value = st.text_area(
            "Вставьте ответ LLM",
            height=200,
            placeholder="Вставьте сюда ответ от LLM...",
            key='llm_response',
            label_visibility="collapsed"
        )
        
        col_unmask, col_clear_llm = st.columns([1, 1])
        with col_unmask:
            if st.button("🔓 Расшифровать", type="primary", use_container_width=True):
                if st.session_state.llm_response and st.session_state.masking_dictionary:
                    # TODO: Здесь вызывается твоя функция расшифровки
                    st.session_state.unmasked_response = unmask_text(
                        st.session_state.llm_response,
                        st.session_state.masking_dictionary
                    )
                    st.success("✅ Ответ расшифрован!")
                    st.rerun()
                elif not st.session_state.masking_dictionary:
                    st.warning("⚠️ Нет словаря для расшифровки. Сначала сгенерируйте замаскированный промпт.")
                else:
                    st.warning("⚠️ Введите ответ LLM")
        
        with col_clear_llm:
            if st.button("🗑️ Очистить", key="clear_llm", use_container_width=True,
                        disabled=not st.session_state.llm_response,
                        on_click=lambda: st.session_state.update({
                            'llm_response': '', 
                            'unmasked_response': ''
                        })):
                pass

    with col_llm_right:
        st.markdown("**Расшифрованный ответ**")
        
        if st.session_state.unmasked_response:
            st.text_area(
                "Расшифрованный текст",
                value=st.session_state.unmasked_response,
                height=200,
                disabled=True,
                label_visibility="collapsed"
            )
            
            if st.button("📋 Копировать расшифрованный", key="copy_unmasked", use_container_width=True):
                copy_to_clipboard(st.session_state.unmasked_response, "copy_unmasked")
                st.toast("✅ Скопировано!")
        else:
            st.info("👈 Вставьте ответ LLM и нажмите 'Расшифровать'")

# Нижняя панель - информация в сайдбаре
st.markdown("---")

# Информация в сайдбаре
st.sidebar.markdown("### 📊 О приложении")
st.sidebar.info("""
**Prompt Builder v1.0**

Приложение для построения промптов с:
- 📚 Версионированием системных промптов;
- 🔍 Контекстным поиском (RAG) по запросу клиента;
- 🎭 Маскированием конфиденциальных данных;
- 🔓 Обратной расшифровкой замаскированного текста в ответах LLM.
""")

st.sidebar.markdown("### 📈 Статистика")
st.sidebar.metric("Версий системного промпта:", len(st.session_state.prompt_versions))
st.sidebar.metric("Длина системного промпта (символов):", f"{len(st.session_state.system_prompt or '')}")
st.sidebar.metric("Длина запроса (символов):", f"{len(st.session_state.user_query or '')}")
st.sidebar.metric("Токенов в финальном промпте:", st.session_state.token_count)

if st.session_state.enable_masking:
    st.sidebar.metric("Замаскированных элементов:", len(st.session_state.masking_dictionary))

if st.session_state.current_version:
    st.sidebar.success(f"🟢 Активная версия системного промпта: {st.session_state.current_version}")

# Показываем текущий словарь маскирования в сайдбаре
if st.session_state.masking_dictionary:
    with st.sidebar.expander("🔍 Текущий словарь замен"):
        for mask, original in st.session_state.masking_dictionary.items():
            st.text(f"{mask} → {original}")

if __name__ == "__main__":
    pass