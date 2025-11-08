import tkinter as tk
from tkinter import ttk

class App(tk.Tk):
    """
    Основной класс приложения, который создает и управляет главным окном и всеми виджетами.
    """
    def __init__(self):
        super().__init__()
        self.title("SQL Prompt Builder")
        self.geometry("1200x800")

        self._create_widgets()

    def _create_widgets(self):
        """
        Создает и размещает все виджеты в главном окне.
        """
        # --- Верхняя панель ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X, side=tk.TOP)

        self.system_prompt_label = ttk.Label(top_frame, text="Системный промпт:")
        self.system_prompt_label.pack(fill=tk.X, pady=5)

        self.system_prompt_text = tk.Text(top_frame, height=5, wrap=tk.WORD)
        self.system_prompt_text.pack(fill=tk.X, expand=True, pady=5)
        self.system_prompt_text.insert("1.0", "Это поле для системного промпта.")

        self.toggle_system_prompt_button = ttk.Button(top_frame, text="Скрыть", command=self.toggle_system_prompt)
        self.toggle_system_prompt_button.pack(anchor=tk.W, pady=5)

        namespace_frame = ttk.Frame(top_frame)
        namespace_frame.pack(fill=tk.X, pady=5)
        
        self.namespace_label = ttk.Label(namespace_frame, text="Namespace:")
        self.namespace_label.pack(side=tk.LEFT, padx=(0, 5))

        self.namespace_combobox = ttk.Combobox(namespace_frame, values=[], state="readonly")
        self.namespace_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.update_db_button = ttk.Button(top_frame, text="Обновить векторную БД", command=self.on_update_db_click)
        self.update_db_button.pack(side=tk.RIGHT, pady=5, padx=5)

        # --- Центральная панель ---
        center_frame = ttk.Frame(self, padding="10")
        center_frame.pack(fill=tk.BOTH, expand=True)
        center_frame.grid_columnconfigure(0, weight=1)
        center_frame.grid_columnconfigure(1, weight=1)
        center_frame.grid_rowconfigure(0, weight=1)

        # Левая часть
        left_frame = ttk.LabelFrame(center_frame, text="Мой запрос", padding="10")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self.user_query_text = tk.Text(left_frame, wrap=tk.WORD)
        self.user_query_text.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.clear_user_query_button = ttk.Button(left_frame, text="Очистить", command=self.clear_user_query)
        self.clear_user_query_button.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 2))

        self.copy_user_query_button = ttk.Button(left_frame, text="Копировать", command=self.copy_user_query)
        self.copy_user_query_button.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(2, 0))

        # Правая часть
        right_frame = ttk.LabelFrame(center_frame, text="Готовый промпт", padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.final_prompt_text = tk.Text(right_frame, wrap=tk.WORD, state="disabled")
        self.final_prompt_text.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.clear_final_prompt_button = ttk.Button(right_frame, text="Очистить", command=self.clear_final_prompt)
        self.clear_final_prompt_button.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 2))

        self.copy_final_prompt_button = ttk.Button(right_frame, text="Копировать", command=self.copy_final_prompt)
        self.copy_final_prompt_button.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(2, 0))

        self.token_counter_label = ttk.Label(right_frame, text="0 / 128000")
        self.token_counter_label.grid(row=2, column=0, columnspan=2, sticky="e", pady=(5, 0))

        # --- Нижняя панель ---
        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.generate_button = ttk.Button(bottom_frame, text="Сгенерировать", command=self.on_generate_click)
        self.generate_button.pack(expand=True)

    # --- Функции-заглушки ---

    def toggle_system_prompt(self):
        """
        Скрывает или показывает поле системного промпта.
        """
        if self.system_prompt_text.winfo_viewable():
            self.system_prompt_text.pack_forget()
            self.system_prompt_label.pack_forget()
            self.toggle_system_prompt_button.config(text="Показать")
        else:
            self.system_prompt_label.pack(fill=tk.X, pady=5, before=self.toggle_system_prompt_button)
            self.system_prompt_text.pack(fill=tk.X, expand=True, pady=5, before=self.toggle_system_prompt_button)
            self.toggle_system_prompt_button.config(text="Скрыть")
        print("Кнопка 'Скрыть/Показать' нажата")

    def on_update_db_click(self):
        print("Кнопка 'Обновить векторную БД' нажата")

    def clear_user_query(self):
        self.user_query_text.delete("1.0", tk.END)
        print("Кнопка 'Очистить' (Мой запрос) нажата")

    def copy_user_query(self):
        self.clipboard_clear()
        self.clipboard_append(self.user_query_text.get("1.0", tk.END))
        print("Кнопка 'Копировать' (Мой запрос) нажата")

    def clear_final_prompt(self):
        self.final_prompt_text.config(state="normal")
        self.final_prompt_text.delete("1.0", tk.END)
        self.final_prompt_text.config(state="disabled")
        print("Кнопка 'Очистить' (Готовый промпт) нажата")

    def copy_final_prompt(self):
        self.clipboard_clear()
        self.clipboard_append(self.final_prompt_text.get("1.0", tk.END))
        print("Кнопка 'Копировать' (Готовый промпт) нажата")

    def on_generate_click(self):
        print("Кнопка 'Сгенерировать' нажата")


if __name__ == "__main__":
    app = App()
    app.mainloop()