import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    """
    Основной класс приложения, который создает и управляет главным окном и всеми виджетами.
    """

    def __init__(self):
        super().__init__()
        # Переопределяем заголовок главного окна
        self.title("SQL Prompt Builder")
        # Переопределяем начальные размеры главного окна
        self.geometry("1200x800")

        # --- Создание и применение стиля для PanedWindow ---
        style = ttk.Style()
        # Настраиваем стиль для разделителя (sash) PanedWindow
        # sashrelief - стиль границы,borderwidth - ширина границы
        style.configure("TPanedwindow.Sash", relief=tk.FLAT)
        style.configure("TPanedwindow", background="#FFFFFF")

        self._create_widgets()


    # Переопределяем метод для создания виджетов
    def _create_widgets(self):
        """
        Создает и размещает все виджеты в главном окне.
        """

        # --- Основная архитектура PanedWindow ---

        # Создаем основной фрейм приложения
        main_frame = ttk.Frame(self, padding="5")
        # Размещаем основной фрейм, растягивая по обеим осям
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем вертикальную PanedWindow для изменения высоты между верхней и центральной частями
        self.vertical_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        self.vertical_paned.pack(fill=tk.BOTH, expand=True)
        
        # Создаем фрейм для верхней части (системный промпт)
        self.top_pane_frame = ttk.Frame(self.vertical_paned, padding="10")
        self.vertical_paned.add(self.top_pane_frame, weight=1)
        
        # Настраиваем сетку верхнего фрейма для динамического изменения размера
        self.top_pane_frame.grid_rowconfigure(1, weight=1)  # Строка с текстовым полем может растягиваться
        
        # Создаем центральный фрейм для основного содержимого
        self.center_frame = ttk.Frame(self.vertical_paned, padding="10")
        self.vertical_paned.add(self.center_frame, weight=3)
        
        # Создаем горизонтальную PanedWindow для центральной части
        self.horizontal_paned = ttk.PanedWindow(self.center_frame, orient=tk.HORIZONTAL)
        self.horizontal_paned.pack(fill=tk.BOTH, expand=True)

        # --- Верхняя панель (Системный промпт) ---

        # Настраиваем веса строк верхнего фрейма
        self.top_pane_frame.grid_rowconfigure(1, weight=1)  # Строка с текстовым полем может растягиваться
        self.top_pane_frame.grid_columnconfigure(0, weight=1)  # Колонка может растягиваться по горизонтали

        # Создаем метку для поля системного промпта (строка 0)
        self.system_prompt_label = ttk.Label(self.top_pane_frame, text="Системный промпт:")
        self.system_prompt_label.grid(row=0, column=0, sticky="ew", pady=5)

        # Создаем фрейм для текстового поля системного промпта и скроллбара (строка 1)
        self.system_prompt_frame = ttk.Frame(self.top_pane_frame)
        self.system_prompt_frame.grid(row=1, column=0, sticky="nsew", pady=5)

        # Настраиваем веса для фрейма текстового поля
        self.system_prompt_frame.grid_rowconfigure(0, weight=1)
        self.system_prompt_frame.grid_columnconfigure(0, weight=1)

        # Создаем скроллбар
        system_prompt_scrollbar = ttk.Scrollbar(self.system_prompt_frame)
        system_prompt_scrollbar.grid(row=0, column=1, sticky="ns")

        # Создаем текстовое поле для системного промпта
        self.system_prompt_text = tk.Text(self.system_prompt_frame, wrap=tk.WORD, yscrollcommand=system_prompt_scrollbar.set)
        self.system_prompt_text.grid(row=0, column=0, sticky="nsew")
        system_prompt_scrollbar.config(command=self.system_prompt_text.yview)

        # Вставляем текст по умолчанию в поле системного промпта
        prompt_text = "Это поле для системного промпта."
        self.system_prompt_text.insert("1.0", prompt_text)

        # Привязываем события к полю текстового поля системного промпта
        self.system_prompt_text.bind("<FocusIn>", lambda event: self.clear_placeholder(prompt_text))
        self.system_prompt_text.bind("<FocusOut>", lambda event: self.restore_placeholder(prompt_text))

        # Фрейм для кнопок управления системным промптом (строка 2)
        system_prompt_buttons_frame = ttk.Frame(self.top_pane_frame)
        system_prompt_buttons_frame.grid(row=2, column=0, sticky="ew", pady=5)

        # Создаем кнопку для скрытия/показа системного промпта
        self.toggle_system_prompt_button = ttk.Button(system_prompt_buttons_frame, text="Скрыть", command=self.toggle_system_prompt)
        self.toggle_system_prompt_button.pack(side=tk.LEFT, padx=(0, 5))

        # Создаем кнопку "Очистить" для поля системного промпта
        self.clear_system_prompt_button = ttk.Button(system_prompt_buttons_frame, text="Очистить", command=self.clear_system_prompt)
        self.clear_system_prompt_button.pack(side=tk.LEFT, padx=(0, 5))

        # Создаем кнопку "Копировать" для поля системного промпта
        self.copy_system_prompt_button = ttk.Button(system_prompt_buttons_frame, text="Копировать", command=self.copy_system_prompt)
        self.copy_system_prompt_button.pack(side=tk.LEFT)

        # Создаем фрейм для пространства имен (namespace) (строка 3)
        namespace_frame = ttk.Frame(self.top_pane_frame)
        namespace_frame.grid(row=3, column=0, sticky="ew", pady=5)
          
        # Создаем метку для выпадающего списка пространства имен
        self.namespace_label = ttk.Label(namespace_frame, text="Namespace:")
        # Размещаем метку слева с отступом справа
        self.namespace_label.pack(side=tk.LEFT, padx=(0, 5))

        # Создаем выпадающий список для пространства имен
        self.namespace_combobox = ttk.Combobox(namespace_frame, values=[], state="readonly")
        # Размещаем выпадающий список слева, растягивая по горизонтали
        self.namespace_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Создаем кнопку "Обновить векторную БД"
        self.update_db_button = ttk.Button(namespace_frame, text="Обновить векторную БД", command=self.on_update_db_click)
        # Размещаем кнопку справа с отступами по вертикали и горизонтали
        self.update_db_button.pack(side=tk.RIGHT, padx=(15, 0))

        # --- Центральная панель ---

        # Левая часть - "Мой запрос"
        left_frame = ttk.LabelFrame(self.horizontal_paned, text="Мой запрос", padding="10")
        self.horizontal_paned.add(left_frame, weight=1)
        # Настраиваем вес первой строки сетки левого фрейма
        left_frame.grid_rowconfigure(0, weight=1)
        # Настраиваем вес первой колонки сетки левого фрейма
        left_frame.grid_columnconfigure(0, weight=1)

        # Создаем фрейм для текстового поля и скроллбара
        user_query_frame = ttk.Frame(left_frame)
        user_query_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Создаем скроллбар
        user_query_scrollbar = ttk.Scrollbar(user_query_frame)
        user_query_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Создаем текстовое поле для пользовательского запроса
        self.user_query_text = tk.Text(user_query_frame, wrap=tk.WORD, yscrollcommand=user_query_scrollbar.set)
        self.user_query_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        user_query_scrollbar.config(command=self.user_query_text.yview)

        # Создаем кнопку "Очистить" для поля пользовательского запроса
        self.clear_user_query_button = ttk.Button(left_frame, text="Очистить", command=self.clear_user_query)
        # Размещаем кнопку в сетке, растягивая по горизонтали
        self.clear_user_query_button.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 2))

        # Создаем кнопку "Копировать" для поля пользовательского запроса
        self.copy_user_query_button = ttk.Button(left_frame, text="Копировать", command=self.copy_user_query)
        # Размещаем кнопку в сетке, растягивая по горизонтали
        self.copy_user_query_button.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(2, 0))

        # Правая часть - "Готовый промпт"
        right_frame = ttk.LabelFrame(self.horizontal_paned, text="Готовый промпт", padding="10")
        self.horizontal_paned.add(right_frame, weight=1)
        # Настраиваем вес первой строки сетки правого фрейма
        right_frame.grid_rowconfigure(0, weight=1)
        # Настраиваем вес первой колонки сетки правого фрейма
        right_frame.grid_columnconfigure(0, weight=1)

        # Создаем фрейм для текстового поля и скроллбара
        final_prompt_frame = ttk.Frame(right_frame)
        final_prompt_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Создаем скроллбар
        final_prompt_scrollbar = ttk.Scrollbar(final_prompt_frame)
        final_prompt_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Создаем текстовое поле для готового промпта (изначально неактивное)
        self.final_prompt_text = tk.Text(final_prompt_frame, wrap=tk.WORD, state="disabled", yscrollcommand=final_prompt_scrollbar.set)
        self.final_prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        final_prompt_scrollbar.config(command=self.final_prompt_text.yview)

        # Создаем кнопку "Очистить" для поля готового промпта
        self.clear_final_prompt_button = ttk.Button(right_frame, text="Очистить", command=self.clear_final_prompt)
        # Размещаем кнопку в сетке, растягивая по горизонтали
        self.clear_final_prompt_button.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 2))

        # Создаем кнопку "Копировать" для поля готового промпта
        self.copy_final_prompt_button = ttk.Button(right_frame, text="Копировать", command=self.copy_final_prompt)
        # Размещаем кнопку в сетке, растягивая по горизонтали
        self.copy_final_prompt_button.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(2, 0))

        # Создаем метку для счетчика токенов
        self.token_counter_label = ttk.Label(right_frame, text="0 / 128000")
        # Размещаем метку в сетке, выравнивая по правому краю
        self.token_counter_label.grid(row=2, column=0, columnspan=2, sticky="e", pady=(5, 0))

        # --- Нижняя панель ---

        # Создаем нижний фрейм с отступами
        bottom_frame = ttk.Frame(self, padding="10")
        # Размещаем нижний фрейм внизу окна, растягивая по горизонтали
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Создаем кнопку "Сгенерировать"
        self.generate_button = ttk.Button(bottom_frame, text="Сгенерировать", command=self.on_generate_click)
        # Размещаем кнопку, растягивая ее, чтобы она заняла доступное место
        self.generate_button.pack(expand=True)

    # --- Функции-заглушки ---


    # Работа с подсказками ввода текста
    def clear_placeholder(self, text):
        """функция очистки текстового поля"""

        if self.system_prompt_text.get("1.0", "end-1c") == text:
            self.system_prompt_text.delete("1.0", "end")


    def restore_placeholder(self, text):
        """функция авто-заполнения текстового поля"""

        if not self.system_prompt_text.get("1.0", "end-1c").strip():
            self.system_prompt_text.insert("1.0", text)


    # Определяем метод для скрытия/показа системного промпта
    def toggle_system_prompt(self):
        """
        Скрывает или показывает поле системного промпта.
        """

        # Проверяем, скрыт ли в данный момент системный промпт
        if not hasattr(self, 'is_system_prompt_hidden'):
            self.is_system_prompt_hidden = False
        
        if self.is_system_prompt_hidden:
            # Если был скрыт, то показываем на исходных позициях
            self.system_prompt_label.grid(row=0, column=0, sticky="ew", pady=5)
            self.system_prompt_frame.grid(row=1, column=0, sticky="nsew", pady=5)
            # Настраиваем вес строки, чтобы она снова могла растягиваться
            self.top_pane_frame.grid_rowconfigure(1, weight=1)

            self.toggle_system_prompt_button.config(text="Скрыть")
            self.is_system_prompt_hidden = False
        else:
            # Если был видим, то скрываем
            self.system_prompt_label.grid_forget()
            self.system_prompt_frame.grid_forget()
            # Убираем вес у строки, чтобы она "сжалась"
            self.top_pane_frame.grid_rowconfigure(1, weight=0)
            self.toggle_system_prompt_button.config(text="Показать")
            self.is_system_prompt_hidden = True

        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Скрыть/Показать' нажата")


    # Определяем метод-обработчик нажатия на кнопку "Обновить векторную БД"
    def on_update_db_click(self):
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Обновить векторную БД' нажата")


    # Определяем метод для очистки поля пользовательского запроса
    def clear_system_prompt(self):
        # Удаляем весь текст из поля от начала ("1.0") до конца (tk.END)
        self.system_prompt_text.delete("1.0", tk.END)
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Очистить' (Системный промпт) нажата")


    # Определяем метод для копирования текста из поля пользовательского запроса
    def copy_system_prompt(self):
        # Очищаем буфер обмена
        self.clipboard_clear()
        # Добавляем в буфер обмена весь текст из поля
        self.clipboard_append(self.system_prompt_text.get("1.0", tk.END))
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Копировать' (Системный промпт) нажата")


    # Определяем метод для очистки поля пользовательского запроса
    def clear_user_query(self):
        # Удаляем весь текст из поля от начала ("1.0") до конца (tk.END)
        self.user_query_text.delete("1.0", tk.END)
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Очистить' (Мой запрос) нажата")


    # Определяем метод для копирования текста из поля пользовательского запроса
    def copy_user_query(self):
        # Очищаем буфер обмена
        self.clipboard_clear()
        # Добавляем в буфер обмена весь текст из поля
        self.clipboard_append(self.user_query_text.get("1.0", tk.END))
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Копировать' (Мой запрос) нажата")


    # Определяем метод для очистки поля готового промпта
    def clear_final_prompt(self):
        # Включаем режим редактирования поля
        self.final_prompt_text.config(state="normal")
        # Удаляем весь текст из поля
        self.final_prompt_text.delete("1.0", tk.END)
        # Выключаем режим редактирования поля
        self.final_prompt_text.config(state="disabled")
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Очистить' (Готовый промпт) нажата")


    # Определяем метод для копирования текста из поля готового промпта
    def copy_final_prompt(self):
        # Очищаем буфер обмена
        self.clipboard_clear()
        # Добавляем в буфер обмена весь текст из поля
        self.clipboard_append(self.final_prompt_text.get("1.0", tk.END))
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Копировать' (Готовый промпт) нажата")


    # Определяем метод-обработчик нажатия на кнопку "Сгенерировать"
    def on_generate_click(self):
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Сгенерировать' нажата")


# Проверяем, запущен ли этот скрипт напрямую (а не импортирован)
if __name__ == "__main__":
    # Создаем экземпляр нашего приложения
    app = App()
    # Запускаем главный цикл обработки событий приложения
    app.mainloop()
