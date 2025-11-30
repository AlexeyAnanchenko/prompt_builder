import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Callable, Dict
from utils.helpers import copy_to_clipboard
from config.settings import MESSAGES
from utils.logger import setup_logger

# Настраиваем логгер для модуля
logger = setup_logger(__name__)


def render_animated_header() -> None:
    """Рендерит анимированный заголовок приложения"""
    logger.info("Рендер анимированного заголовка")
    components.html("""
<style>
    .animated-title {
        text-align: center;
        font-size: 3em;
        font-weight: 700;
        color: #343a40;
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
    
    .title-text {
        background: linear-gradient(135deg, #5a7fb8 0%, #6b9d7d 100%);
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


def render_button_pair(
    clear_key: str,
    copy_key: str,
    text_to_copy: Optional[str],
    clear_callback: Optional[Callable] = None
) -> None:
    """
    Рендерит пару кнопок Очистить/Копировать
    """
    col_clear, col_copy = st.columns([1, 1])
    
    with col_clear:
        if st.button(
            "🗑️ Очистить",
            key=clear_key,
            use_container_width=True,
            disabled=not text_to_copy,
            on_click=clear_callback
        ):
            pass
    
    with col_copy:
        if text_to_copy:
            if st.button("📋 Копировать", key=copy_key, use_container_width=True):
                copy_to_clipboard(text_to_copy, copy_key)
                logger.info(f"Текст скопирован в буфер обмена (ключ: {copy_key})")
                st.toast(MESSAGES["toast_copied"])
        else:
            st.button(
                "📋 Копировать",
                key=f"{copy_key}_disabled",
                disabled=True,
                use_container_width=True
            )


def render_step_toggle_button(
    step_number: int,
    title: str,
    state_key: str
) -> None:
    """
    Рендерит кнопку переключения видимости шага
    """
    icon = "▼" if st.session_state.get(state_key, False) else "▶"
    
    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
    # Расширенный список эмодзи, чтобы не вылетала ошибка при step_number=4
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    # Безопасное получение эмодзи
    if 0 <= step_number - 1 < len(emojis):
        emoji = emojis[step_number - 1]
    else:
        emoji = f"#{step_number}" # Fallback, если шагов будет больше 10
    # -------------------------
    
    if st.button(
        f'{emoji} {title} {icon}',
        key=f'step{step_number}_toggle',
        use_container_width=True,
        type='primary'
    ):
        st.session_state[state_key] = not st.session_state.get(state_key, False)
        st.rerun()


def render_token_counter(token_count: int, max_tokens: int) -> None:
    """
    Рендерит счётчик токенов с прогресс-баром
    """
    progress = min(token_count / max_tokens, 1.0)
    
    col_tokens, col_bar = st.columns([1, 3])
    with col_tokens:
        st.caption(f"**Токены:** {token_count:,} / {max_tokens:,}")
    with col_bar:
        st.progress(progress)


def render_sidebar_info() -> None:
    """Рендерит информацию в сайдбаре"""
    st.sidebar.markdown("### 📊 О приложении")
    st.sidebar.info("""
**Prompt Builder v2.0**

Приложение для построения промптов с:
- 📚 Версионированием системных промптов
- 🧙‍♂️ Генерацией SQL-контекста
- 🎭 Маскированием конфиденциальных данных
- 🔓 Обратной расшифровкой ответов
""")
    
    st.sidebar.markdown("### 📈 Статистика")
    st.sidebar.metric(
        "Версий системного промпта:",
        len(st.session_state.get('prompt_versions', {}))
    )
    st.sidebar.metric(
        "Длина системного промпта (символов):",
        f"{len(st.session_state.get('system_prompt', '') or '')}"
    )
    st.sidebar.metric(
        "Токенов в финальном промпте:",
        st.session_state.get('token_count', 0)
    )
    
    if st.session_state.get('enable_masking'):
        st.sidebar.metric(
            "Замаскированных элементов:",
            len(st.session_state.get('masking_dictionary', {}))
        )
    
    if st.session_state.get('current_version'):
        st.sidebar.success(
            f"🟢 Активная версия: {st.session_state['current_version']}"
        )


def render_version_preview(version_name: str, version_data: Dict) -> Optional[str]:
    """
    Рендерит превью версии промпта
    """
    col_info, col_actions = st.columns([3, 1])
    
    with col_info:
        is_current = version_name == st.session_state.get('current_version')
        status = "🟢 Активна" if is_current else ""
        
        st.markdown(f"**{version_name}** {status}")
        st.caption(
            f"Создана: {version_data['created']} | "
            f"Изменена: {version_data['modified']}"
        )
        
        with st.expander("🔎 Показать текст промпта", expanded=False):
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
            if st.button(
                "📥",
                key=f"load_{version_name}",
                help="Загрузить эту версию",
                use_container_width=True
            ):
                return "load"
        with col_del:
            if st.button(
                "🗑️",
                key=f"delete_{version_name}",
                help="Удалить эту версию",
                use_container_width=True
            ):
                return "delete"
    
    st.markdown("---")
    return None