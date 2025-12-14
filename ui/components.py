import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Callable, Dict, Any
from utils.helpers import copy_to_clipboard
from config.settings import MESSAGES
from utils.logger import setup_logger

# Настраиваем логгер для модуля компонентов
logger = setup_logger(__name__)


def render_animated_header() -> None:
    """
    Рендерит анимированный заголовок приложения с эффектом печатающей машинки.
    Использует components.html для внедрения JavaScript.
    """
    logger.debug("Рендер анимированного заголовка")
    
    # HTML/CSS/JS код взят из оригинала без изменений логики, 
    # чтобы сохранить визуальный эффект.
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
        transform: translateX(-15px);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .typewriter-emoji {
        font-size: 1.2em;
        margin-right: 15px;
        cursor: pointer;
        flex-shrink: 0;
        position: relative;
        top: -8px;
    }
    
    .title-wrapper {
        display: inline-block;
        position: relative;
    }
    
    .title-text {
        background: linear-gradient(135deg, #5a7fb8 0%, #6b9d7d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: inline-block;
    }
    
    .cursor {
        display: inline-block;
        width: 3px;
        height: 1em;
        background-color: #5a7fb8;
        margin-left: 2px;
        vertical-align: text-bottom;
        opacity: 0;
    }
    
    .cursor.blink {
        animation: blink-caret 0.75s step-end infinite;
        opacity: 1;
    }
    
    @keyframes blink-caret {
        from, to { opacity: 1; }
        50% { opacity: 0; }
    }
</style>

<div class="animated-title">
    <span class="typewriter-emoji" id="typewriter">⌨️</span>
    <div class="title-wrapper">
        <span class="title-text" id="titleText">Prompt Builder</span>
        <span class="cursor" id="cursor"></span>
    </div>
</div>

<script>
    const typewriter = document.getElementById('typewriter');
    const titleText = document.getElementById('titleText');
    const cursor = document.getElementById('cursor');
    const fullText = 'Prompt Builder';
    
    function playTypingAnimation() {
        // Показываем курсор
        cursor.classList.add('blink');
        
        // Сброс текста
        titleText.textContent = '';
        
        // Печатаем по буквам
        let i = 0;
        const typeInterval = setInterval(() => {
            if (i < fullText.length) {
                titleText.textContent += fullText.charAt(i);
                i++;
            } else {
                clearInterval(typeInterval);
                // Убираем курсор через секунду
                setTimeout(() => {
                    cursor.classList.remove('blink');
                }, 1000);
            }
        }, 100);
    }
    
    // Запускаем анимацию при загрузке страницы
    window.addEventListener('load', () => {
        setTimeout(playTypingAnimation, 300);
    });
    
    // Запускаем анимацию при клике на клавиатуру
    typewriter.addEventListener('click', playTypingAnimation);
</script>
""", height=100)


def render_button_pair(
    clear_key: str,
    copy_key: str,
    text_to_copy: Optional[str],
    clear_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Рендерит пару кнопок "Очистить" и "Копировать" в две колонки.
    
    Args:
        clear_key: Уникальный ключ для кнопки очистки.
        copy_key: Уникальный ключ для кнопки копирования.
        text_to_copy: Текст, который будет скопирован (если None, кнопка неактивна).
        clear_callback: Функция обратного вызова для очистки.
    """
    col_clear, col_copy = st.columns([1, 1])
    
    with col_clear:
        if st.button(
            "🗑️ Очистить",
            key=clear_key,
            use_container_width=True,
            disabled=not text_to_copy, # Блокируем, если нечего очищать
            on_click=clear_callback
        ):
            logger.info(f"Нажата кнопка очистки: {clear_key}")
            # Callback выполнится самим Streamlit
            pass
    
    with col_copy:
        if text_to_copy:
            if st.button("📋 Копировать", key=copy_key, use_container_width=True):
                copy_to_clipboard(text_to_copy, copy_key)
                logger.info(f"Текст скопирован в буфер (ключ: {copy_key})")
                st.toast(MESSAGES["toast_copied"])
        else:
            # Рендерим неактивную кнопку-заглушку
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
    Рендерит большую кнопку переключения видимости шага (Step 1, 2, 3).
    
    Args:
        step_number: Номер шага (для иконки 1️⃣).
        title: Текст на кнопке.
        state_key: Ключ session_state, управляющий видимостью контента.
    """
    # Определяем текущее состояние (свернуто/развернуто)
    is_open = st.session_state.get(state_key, False)
    icon = "▼" if is_open else "▶"
    
    # Выбор иконки-цифры
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    emoji = emojis[step_number - 1] if 0 <= step_number - 1 < len(emojis) else f"#{step_number}"
    
    # Кнопка 'primary' стиля (синяя градиентная)
    if st.button(
        f'{emoji} {title} {icon}',
        key=f'step{step_number}_toggle',
        use_container_width=True,
        type='primary'
    ):
        # Инвертируем состояние при клике
        new_state = not is_open
        st.session_state[state_key] = new_state
        logger.info(f"Переключение шага {step_number}: {'Развернут' if new_state else 'Свернут'}")
        st.rerun()


def render_token_counter(token_count: int, max_tokens: int) -> None:
    """
    Рендерит счётчик токенов с визуальным прогресс-баром.
    """
    # Ограничиваем прогресс единицей (100%), чтобы не было ошибки визуализации
    progress = min(token_count / max_tokens, 1.0)
    
    col_tokens, col_bar = st.columns([1, 3])
    with col_tokens:
        st.caption(f"**Токены:** {token_count:,} / {max_tokens:,}")
    with col_bar:
        st.progress(progress)


def render_sidebar_info() -> None:
    """Рендерит информационную панель в боковом меню (Sidebar)."""
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
    
    # Метрика: Количество версий
    versions = st.session_state.get('prompt_versions', {})
    st.sidebar.metric(
        "Версий системного промпта:",
        len(versions)
    )
    
    # Метрика: Длина текста
    system_prompt_length = len(st.session_state.get('system_prompt', '') or '')
    st.sidebar.metric(
        "Длина системного промпта (символов):",
        f"{system_prompt_length:,}"
    )
    
    # Метрика: Токены
    token_count = st.session_state.get('token_count', 0)
    if token_count > 0:
        st.sidebar.metric("Токенов в промпте:", f"{token_count:,}")
    else:
        st.sidebar.metric("Токенов в промпте:", "—")
    
    # Метрика: Маски
    masking_dict = st.session_state.get('masking_dictionary', {})
    if masking_dict:
        st.sidebar.metric("Замаскированных элементов:", len(masking_dict))
    
    # Статус активной версии
    current_ver = st.session_state.get('current_version')
    if current_ver:
        st.sidebar.success(f"💡 Активная версия: {current_ver}")


def render_version_preview(version_name: str, version_data: Dict[str, Any]) -> Optional[str]:
    """
    Рендерит превью одной версии промпта в списке загрузки.
    
    Args:
        version_name: Название версии (ключ).
        version_data: Данные версии (prompt, created, modified).
        
    Returns:
        str | None: Возвращает действие ('load', 'delete') или None.
    """
    col_info, col_actions = st.columns([3, 1])
    
    with col_info:
        is_current = version_name == st.session_state.get('current_version')
        status = "(💡 активен)" if is_current else ""
        
        st.markdown(f"**{version_name}** {status}")
        st.caption(
            f"Создана: {version_data.get('created', 'N/A')} | "
            f"Изменена: {version_data.get('modified', 'N/A')}"
        )
        
        with st.expander("🔎 Показать текст промпта", expanded=False):
            st.text_area(
                "Текст промпта",
                value=version_data.get('prompt', ''),
                height=200,
                disabled=True,
                # Уникальный ключ для избежания конфликтов Streamlit
                key=f"preview_{version_name}_{version_data.get('modified', '')}",
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