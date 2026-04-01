import tkinter as tk
from tkinter import ttk, messagebox
import random

class RandomEventApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Моделирование случайных событий")
        self.geometry("900x650")
        self.minsize(800, 600)

        self.style = ttk.Style(self)
        self.style.configure("TLabel", font=("Arial", 11))
        self.style.configure("TButton", font=("Arial", 11))
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.yes_no_frame = YesNoFrame(self.notebook)
        self.magic_ball_frame = MagicBallFrame(self.notebook)

        self.notebook.add(self.yes_no_frame, text='Часть 1')
        self.notebook.add(self.magic_ball_frame, text='Часть 2')


class YesNoFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)

        ttk.Label(self, text='Приложение "Скажи “да” или “нет”"', style="Header.TLabel").pack(anchor="w", pady=(0, 15))

        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", pady=5)

        ttk.Label(input_frame, text="Введите вопрос:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.question_entry = ttk.Entry(input_frame, width=60)
        self.question_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.question_entry.insert(0, "Пойти сегодня в университет?")

        ttk.Label(input_frame, text='Вероятность ответа "Да" (0..1):').grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        self.prob_entry = ttk.Entry(input_frame, width=20)
        self.prob_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.prob_entry.insert(0, "0.5")

        input_frame.columnconfigure(1, weight=1)

        ttk.Button(self, text="Получить ответ", command=self.generate_answer).pack(anchor="w", pady=10)

        self.question_label = ttk.Label(self, text="", font=("Arial", 13, "bold"))
        self.question_label.pack(anchor="w", pady=(10, 5))

        self.answer_label = ttk.Label(self, text="", font=("Arial", 26, "bold"))
        self.answer_label.pack(anchor="center", pady=30)

        explanation = (
            "Логика моделирования:\n"
            "Генерируется случайное число α из [0, 1).\n"
            'Если α < p, то событие "Да" произошло.\n'
            'Иначе произошло событие "Нет".'
        )
        ttk.Label(self, text=explanation, justify="left").pack(anchor="w", pady=10)

    def generate_answer(self):
        question = self.question_entry.get().strip()
        if not question:
            messagebox.showerror("Ошибка", "Введите вопрос.")
            return

        try:
            p = float(self.prob_entry.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Вероятность должна быть числом.")
            return

        if not (0 <= p <= 1):
            messagebox.showerror("Ошибка", 'Вероятность ответа "Да" должна быть в диапазоне от 0 до 1.')
            return

        # alpha = random.random()
        # answer = "ДА!" if alpha < p else "НЕТ!"

        events = [("ДА", p), ("НЕТ", 1 - p)]
        alpha = random.random()

        for name, prob in events:
            alpha -= prob
            if alpha <= 0:
                answer = name
                break

        self.question_label.config(text=f"Вопрос: {question}")
        self.answer_label.config(text=f"Ответ: {answer}")


class MagicBallFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)

        ttk.Label(self, text='Приложение "Шар предсказаний" (Magic 8-Ball)', style="Header.TLabel").pack(anchor="w", pady=(0, 15))

        self.events = [
            ("Бесспорно", 0.15),
            ("Вероятнее всего", 0.15),
            ("Хорошие перспективы", 0.15),
            ("Пока не ясно", 0.20),
            ("Спроси позже", 0.10),
            ("Сомнительно", 0.10),
            ("Мой ответ: нет", 0.10),
            ("Очень маловероятно", 0.05),
        ]

        self.stats = [0] * len(self.events)
        self.total_count = 0

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=5)

        ttk.Label(top_frame, text="Введите вопрос:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.question_entry = ttk.Entry(top_frame, width=60)
        self.question_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.question_entry.insert(0, "Стоит ли начинать новый проект?")

        top_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Предсказать", command=self.predict).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Очистить статистику", command=self.reset_stats).pack(side="left")

        self.question_label = ttk.Label(self, text="", font=("Arial", 12, "bold"))
        self.question_label.pack(anchor="w", pady=(10, 5))

        self.answer_label = ttk.Label(self, text="", font=("Arial", 22, "bold"))
        self.answer_label.pack(anchor="center", pady=20)

        ttk.Label(self, text="Статистика результатов:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(15, 5))

        columns = ("prediction", "probability", "count", "frequency")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("prediction", text="Предсказание")
        self.tree.heading("probability", text="Теор. вероятность")
        self.tree.heading("count", text="Частота")
        self.tree.heading("frequency", text="Отн. частота")

        self.tree.column("prediction", width=280)
        self.tree.column("probability", width=140, anchor="center")
        self.tree.column("count", width=100, anchor="center")
        self.tree.column("frequency", width=120, anchor="center")

        self.update_table()

        explanation = (
            "Логика моделирования:\n"
            "Все ответы образуют полную группу событий с заданными вероятностями.\n"
            "Генерируется α из [0,1), затем определяется интервал,\n"
            "в который попало α. Соответствующее событие считается произошедшим."
        )
        ttk.Label(self, text=explanation, justify="left").pack(anchor="w", pady=10)

    def predict(self):
        question = self.question_entry.get().strip()
        if not question:
            messagebox.showerror("Ошибка", "Введите вопрос.")
            return

        # for event:
        #     alpha -= p
        #     if alpha <= 0:
        #         return event

        alpha = random.random()
        cumulative = 0.0
        chosen_index = len(self.events) - 1

        for i, (_, probability) in enumerate(self.events):
            cumulative += probability
            if alpha < cumulative:
                chosen_index = i
                break

        prediction = self.events[chosen_index][0]
        self.stats[chosen_index] += 1
        self.total_count += 1

        self.question_label.config(text=f"Вопрос: {question}")
        self.answer_label.config(text=f"Предсказание: {prediction}")
        self.update_table()

    def reset_stats(self):
        self.stats = [0] * len(self.events)
        self.total_count = 0
        self.question_label.config(text="")
        self.answer_label.config(text="")
        self.update_table()

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, (prediction, probability) in enumerate(self.events):
            count = self.stats[i]
            frequency = count / self.total_count if self.total_count > 0 else 0.0
            self.tree.insert(
                "",
                "end",
                values=(
                    prediction,
                    f"{probability:.2f}",
                    count,
                    f"{frequency:.4f}",
                ),
            )


if __name__ == "__main__":
    app = RandomEventApp()
    app.mainloop()