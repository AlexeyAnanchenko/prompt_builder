import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    """
    Основной класс приложения, который создает и управляет главным окном и всеми виджетами.
    """
    def __init__(self):
        # Вызываем инициализатор родительского класса
        super().__init__()
        # Устанавливаем заголовок главного окна
        self.title("SQL Prompt Builder")
        # Устанавливаем начальные размеры главного окна
        self.geometry("1200x800")

        self._create_widgets()

    # Определяем метод для создания виджетов
    def _create_widgets(self):
        """
        Создает и размещает все виджеты в главном окне.
        """
        # --- Верхняя панель ---
        # Создаем верхний фрейм (рамку) с отступами
        top_frame = ttk.Frame(self, padding="10")
        # Размещаем верхний фрейм вверху окна, растягивая по горизонтали
        top_frame.pack(fill=tk.X, side=tk.TOP)

        # Создаем метку для поля системного промпта
        self.system_prompt_label = ttk.Label(top_frame, text="Системный промпт:")
        # Размещаем метку, растягивая по горизонтали с отступом по вертикали
        self.system_prompt_label.pack(fill=tk.X, pady=5)

        # Создаем текстовое поле для системного промпта
        self.system_prompt_text = tk.Text(top_frame, height=5, wrap=tk.WORD)
        # Размещаем текстовое поле, растягивая по горизонтали с отступом по вертикали
        self.system_prompt_text.pack(fill=tk.X, expand=True, pady=5)
        # Вставляем текст по умолчанию в поле системного промпта
        self.system_prompt_text.insert("1.0", "Это поле для системного промпта.")

        # Создаем кнопку для скрытия/показа системного промпта
        self.toggle_system_prompt_button = ttk.Button(top_frame, text="Скрыть", command=self.toggle_system_prompt)
        # Размещаем кнопку слева с отступом по вертикали
        self.toggle_system_prompt_button.pack(anchor=tk.W, pady=5)

        # Создаем фрейм для пространства имен (namespace)
        namespace_frame = ttk.Frame(top_frame)
        # Размещаем фрейм пространства имен, растягивая по горизонтали с отступом по вертикали
        namespace_frame.pack(fill=tk.X, pady=5)
        
        # Создаем метку для выпадающего списка пространства имен
        self.namespace_label = ttk.Label(namespace_frame, text="Namespace:")
        # Размещаем метку слева с отступом справа
        self.namespace_label.pack(side=tk.LEFT, padx=(0, 5))

        # Создаем выпадающий список для пространства имен
        self.namespace_combobox = ttk.Combobox(namespace_frame, values=[], state="readonly")
        # Размещаем выпадающий список слева, растягивая по горизонтали
        self.namespace_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Создаем кнопку "Обновить векторную БД"
        self.update_db_button = ttk.Button(top_frame, text="Обновить векторную БД", command=self.on_update_db_click)
        # Размещаем кнопку справа с отступами по вертикали и горизонтали
        self.update_db_button.pack(side=tk.RIGHT, pady=5, padx=5)

        # --- Центральная панель ---
        # Создаем центральный фрейм с отступами
        center_frame = ttk.Frame(self, padding="10")
        # Размещаем центральный фрейм, растягивая по обеим осям
        center_frame.pack(fill=tk.BOTH, expand=True)
        # Настраиваем вес первой колонки сетки, чтобы она растягивалась
        center_frame.grid_columnconfigure(0, weight=1)
        # Настраиваем вес второй колонки сетки, чтобы она растягивалась
        center_frame.grid_columnconfigure(1, weight=1)
        # Настраиваем вес первой строки сетки, чтобы она растягивалась
        center_frame.grid_rowconfigure(0, weight=1)

        # Левая часть
        # Создаем фрейм с заголовком "Мой запрос"
        left_frame = ttk.LabelFrame(center_frame, text="Мой запрос", padding="10")
        # Размещаем левый фрейм в сетке, растягивая по всем направлениям
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        # Настраиваем вес первой строки сетки левого фрейма
        left_frame.grid_rowconfigure(0, weight=1)
        # Настраиваем вес первой колонки сетки левого фрейма
        left_frame.grid_columnconfigure(0, weight=1)

        # Создаем текстовое поле для пользовательского запроса
        self.user_query_text = tk.Text(left_frame, wrap=tk.WORD)
        # Размещаем текстовое поле в сетке, растягивая по всем направлениям
        self.user_query_text.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Создаем кнопку "Очистить" для поля пользовательского запроса
        self.clear_user_query_button = ttk.Button(left_frame, text="Очистить", command=self.clear_user_query)
        # Размещаем кнопку в сетке, растягивая по горизонтали
        self.clear_user_query_button.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 2))

        # Создаем кнопку "Копировать" для поля пользовательского запроса
        self.copy_user_query_button = ttk.Button(left_frame, text="Копировать", command=self.copy_user_query)
        # Размещаем кнопку в сетке, растягивая по горизонтали
        self.copy_user_query_button.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(2, 0))

        # Правая часть
        # Создаем фрейм с заголовком "Готовый промпт"
        right_frame = ttk.LabelFrame(center_frame, text="Готовый промпт", padding="10")
        # Размещаем правый фрейм в сетке, растягивая по всем направлениям
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        # Настраиваем вес первой строки сетки правого фрейма
        right_frame.grid_rowconfigure(0, weight=1)
        # Настраиваем вес первой колонки сетки правого фрейма
        right_frame.grid_columnconfigure(0, weight=1)

        # Создаем текстовое поле для готового промпта (изначально неактивное)
        self.final_prompt_text = tk.Text(right_frame, wrap=tk.WORD, state="disabled")
        # Размещаем текстовое поле в сетке, растягивая по всем направлениям
        self.final_prompt_text.grid(row=0, column=0, columnspan=2, sticky="nsew")

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

    # Определяем метод для скрытия/показа системного промпта
    def toggle_system_prompt(self):
        """
        Скрывает или показывает поле системного промпта.
        """
        # Проверяем, видим ли в данный момент текстовое поле системного промпта
        if self.system_prompt_text.winfo_viewable():
            # Если да, то убираем его с экрана
            self.system_prompt_text.pack_forget()
            # Убираем также и метку
            self.system_prompt_label.pack_forget()
            # Меняем текст на кнопке на "Показать"
            self.toggle_system_prompt_button.config(text="Показать")
        # Если поле не видно
        else:
            # Возвращаем метку на экран перед кнопкой
            self.system_prompt_label.pack(fill=tk.X, pady=5, before=self.toggle_system_prompt_button)
            # Возвращаем текстовое поле на экран перед кнопкой
            self.system_prompt_text.pack(fill=tk.X, expand=True, pady=5, before=self.toggle_system_prompt_button)
            # Меняем текст на кнопке обратно на "Скрыть"
            self.toggle_system_prompt_button.config(text="Скрыть")
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Скрыть/Показать' нажата")

    # Определяем метод-обработчик нажатия на кнопку "Обновить векторную БД"
    def on_update_db_click(self):
        # Выводим сообщение в консоль для отладки
        print("Кнопка 'Обновить векторную БД' нажата")

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
