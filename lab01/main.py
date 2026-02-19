import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import math
from dataclasses import dataclass
from typing import List, Tuple
matplotlib.use('TkAgg')

@dataclass
class SimulationResult:
    dt: float
    trajectory: List[Tuple[float, float]]
    speeds: List[float]
    range: float
    max_height: float
    final_speed: float

class BallisticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование полёта тела в атмосфере")
        self.root.geometry("1800x1000")

        self.g = 9.81
        self.mass = 1.0
        self.rho = 1.29
        self.Cd = 0.15
        self.A = 0.01
        self.v0 = 100.0
        self.angle = 45.0

        self.results: List[SimulationResult] = []
        self.anim = None

        # Обычные цвета (как в matplotlib по умолчанию)
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                       '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        self.color_index = 0

        self.build_ui()

    def build_ui(self):
        # Основной контейнер с сеткой 2x2
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        # Настройка весов колонок и строк
        main.grid_columnconfigure(0, weight=6)  # левая колонка (график) - шире
        main.grid_columnconfigure(1, weight=4)  # правая колонка (параметры)
        main.grid_rowconfigure(0, weight=7)     # верхняя строка (график + параметры)
        main.grid_rowconfigure(1, weight=3)     # нижняя строка (таблица + информация)

        # ========== ВЕРХНЯЯ СТРОКА ==========
        # Левая верхняя ячейка - график (теперь только один)
        graph_frame = ttk.LabelFrame(main, text="График траектории", padding=10)
        graph_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        self.figure = Figure(figsize=(12, 7), dpi=100)
        # Создаём только один подграфик для траектории
        self.ax_traj = self.figure.add_subplot(111)

        # Стандартное оформление графика
        self.ax_traj.set_xlabel("Дальность, м")
        self.ax_traj.set_ylabel("Высота, м")
        self.ax_traj.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Правая верхняя ячейка - панель управления
        control_frame = ttk.Frame(main)
        control_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 10))

        # Фрейм параметров запуска
        params_frame = ttk.LabelFrame(control_frame, text="Параметры запуска", padding=15)
        params_frame.pack(fill="x", pady=10)

        params = [
            ("Начальная скорость (м/с)", self.v0),
            ("Угол запуска (°)", self.angle),
            ("Масса тела (кг)", self.mass),
            ("Плотность воздуха (кг/м³)", self.rho),
            ("Коэффициент сопротивления", self.Cd),
            ("Площадь сечения (м²)", self.A),
        ]

        self.entries = {}
        for label, default in params:
            row = ttk.Frame(params_frame)
            row.pack(fill="x", pady=5)

            ttk.Label(row, text=label).pack(side="left")
            entry = ttk.Entry(row, width=12)
            entry.insert(0, str(default))
            entry.pack(side="right")
            self.entries[label] = entry

        ttk.Label(params_frame, text="Шаг моделирования (с)").pack(pady=(10, 0))
        self.dt_entry = ttk.Entry(params_frame, width=12)
        self.dt_entry.insert(0, "0.01")
        self.dt_entry.pack()

        # Кнопки управления
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=20, fill="x")

        ttk.Button(btn_frame, text="Запустить моделирование",
                   command=self.run_simulation).pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Очистить результаты",
                   command=self.clear_results).pack(fill="x", pady=5)

        # ========== НИЖНЯЯ СТРОКА ==========
        # Создаём фрейм для нижней строки, разделённый на две колонки
        bottom_frame = ttk.Frame(main)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        bottom_frame.grid_columnconfigure(0, weight=4)  # таблица (чуть уже)
        bottom_frame.grid_columnconfigure(1, weight=6)  # информация (пошире)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Левая нижняя ячейка - таблица результатов
        table_frame = ttk.LabelFrame(bottom_frame, text="Результаты моделирования", padding=10)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        columns = ("Шаг (с)", "Дальность (м)", "Макс. высота (м)", "Скорость в конце (м/с)", "Время полёта (с)")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Правая нижняя ячейка - информация (широкая)
        info_frame = ttk.LabelFrame(bottom_frame, text="Информация о последнем моделировании", padding=15)
        info_frame.grid(row=0, column=1, sticky="nsew")

        self.info_label = ttk.Label(info_frame, text="Моделирование не проводилось",
                                    justify="left", font=("TkDefaultFont", 11))
        self.info_label.pack(expand=True, fill="both")

    def get_parameters(self):
        try:
            return {
                'v0': float(self.entries["Начальная скорость (м/с)"].get()),
                'angle': float(self.entries["Угол запуска (°)"].get()),
                'mass': float(self.entries["Масса тела (кг)"].get()),
                'rho': float(self.entries["Плотность воздуха (кг/м³)"].get()),
                'Cd': float(self.entries["Коэффициент сопротивления"].get()),
                'A': float(self.entries["Площадь сечения (м²)"].get()),
                'dt': float(self.dt_entry.get())
            }
        except:
            messagebox.showerror("Ошибка", "Некорректные данные")
            return None

    def calculate_drag_force(self, v, params):
        return 0.5 * params['rho'] * params['Cd'] * params['A'] * v ** 2

    def run_simulation(self):
        params = self.get_parameters()
        if params is None:
            return

        dt = params['dt']
        angle_rad = math.radians(params['angle'])

        x, y = 0.0, 0.0
        vx = params['v0'] * math.cos(angle_rad)
        vy = params['v0'] * math.sin(angle_rad)

        trajectory = [(x, y)]
        speeds = [math.sqrt(vx * vx + vy * vy)]
        t = 0.0
        max_height = 0.0

        while y >= 0:
            v = math.sqrt(vx ** 2 + vy ** 2)
            drag = self.calculate_drag_force(v, params)

            ax = -drag * vx / (params['mass'] * v) if v > 0 else 0
            ay = -self.g - drag * vy / (params['mass'] * v) if v > 0 else -self.g

            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt

            trajectory.append((x, y))
            speeds.append(math.sqrt(vx * vx + vy * vy))

            if y > max_height:
                max_height = y

        result = SimulationResult(
            dt=dt,
            trajectory=trajectory,
            speeds=speeds,
            range=x,
            max_height=max_height,
            final_speed=speeds[-1]
        )

        self.results.append(result)
        self.animate_new_trajectory(result)
        self.update_table()
        self.update_info()

    def animate_new_trajectory(self, result):
        xs = [p[0] for p in result.trajectory]
        ys = [p[1] for p in result.trajectory]

        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1

        # Убрали построение графика скорости

        max_frames = 800
        n = len(xs)

        if n > max_frames:
            step = n // max_frames
            xs = xs[::step]
            ys = ys[::step]

        line, = self.ax_traj.plot([], [], color=color, linewidth=2, label=f"dt={result.dt}")
        self.ax_traj.legend()

        self.ax_traj.set_xlim(0, max(xs) * 1.05)
        self.ax_traj.set_ylim(0, max(ys) * 1.05)

        def animate(i):
            line.set_data(xs[:i], ys[:i])
            return line,

        if self.anim and self.anim.event_source:
            self.anim.event_source.stop()

        self.anim = FuncAnimation(
            self.figure,
            animate,
            frames=len(xs),
            interval=1,
            blit=True,
            repeat=False
        )

        self.canvas.draw()

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in self.results:
            flight_time = len(r.trajectory) * r.dt
            self.tree.insert("", "end", values=(
                f"{r.dt:.6f}",
                f"{r.range:.2f}",
                f"{r.max_height:.2f}",
                f"{r.final_speed:.2f}",
                f"{flight_time:.2f}"
            ))

    def update_info(self):
        if not self.results:
            self.info_label.config(text="Моделирование не проводилось")
            return

        r = self.results[-1]
        self.info_label.config(text=(
            f"Последнее моделирование:\n"
            f"Шаг: {r.dt:.6f} с\n"
            f"Дальность: {r.range:.2f} м\n"
            f"Макс. высота: {r.max_height:.2f} м\n"
            f"Скорость в конце: {r.final_speed:.2f} м/с"
        ))

    def clear_results(self):
        self.results.clear()
        self.color_index = 0

        self.ax_traj.clear()

        # Восстанавливаем стандартные подписи и сетку
        self.ax_traj.set_xlabel("Дальность, м")
        self.ax_traj.set_ylabel("Высота, м")
        self.ax_traj.grid(True, alpha=0.3)

        self.canvas.draw()

        self.update_table()
        self.update_info()

def main():
    root = tk.Tk()
    app = BallisticApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()