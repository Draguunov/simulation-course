import sys
import csv
import numpy as np
from scipy.stats import expon # нужен для генерации случайного времени пребывания в состоянии. В непрерывной цепи Маркова время ожидания до следующего перехода имеет экспоненциальное распределение.
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDoubleSpinBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

STYLE = """
QMainWindow, QWidget {
    background-color: #f5f5f7;
    color: #1d1d1f;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTableWidget {
    background-color: white;
    border: 1px solid #d2d2d7;
    gridline-color: #eeeeee;
}
QHeaderView::section {
    background-color: #fbfbfd;
    color: #555555;
    padding: 7px;
    border: 1px solid #d2d2d7;
    font-weight: bold;
}
QPushButton {
    background-color: #2ecc71;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px;
    font-weight: 600;
}
QPushButton:hover { 
    background-color: #27ae60; 
}
QDoubleSpinBox {
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 6px;
}
QFrame#Card {
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 10px;
}
"""

STATE_NAMES = ["Ясно", "Облачно", "Пасмурно"]
STATE_NUMBERS = [1, 2, 3]

class StatCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setStyleSheet("font-weight: bold; color: #555555;")
        self.value = QLabel("—")
        self.value.setStyleSheet("font-size: 14px;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_text(self, text):
        self.value.setText(text)


def build_generator_matrix(rates):
    """Создает матрицу интенсивностей Q. Диагональ считается автоматически."""
    q = np.array(rates, dtype=float)
    n = q.shape[0]

    for i in range(n):
        q[i, i] = 0.0
        if np.any(q[i] < 0):
            raise ValueError("Интенсивности переходов не могут быть отрицательными.")

        row_sum = np.sum(q[i])
        if row_sum <= 0:
            raise ValueError(f"Из состояния {i + 1} должен быть хотя бы один выход.")

        q[i, i] = -row_sum

    return q


def transition_probability_matrix(q):
    """Из матрицы интенсивностей Q получает вероятности выбора следующего состояния."""
    n = q.shape[0]
    p = np.zeros_like(q, dtype=float)

    for i in range(n):
        exit_rate = -q[i, i]
        for j in range(n):
            if i != j:
                p[i, j] = q[i, j] / exit_rate # интенсивность перехода / общая интенсивность выхода

    return p


def stationary_distribution(q):
    """Решает СЛУ для стационарных вероятностей: pi * Q = 0, сумма pi = 1."""
    n = q.shape[0]
    a = q.T.copy()
    b = np.zeros(n)

    a[-1, :] = 1.0
    b[-1] = 1.0

    pi = np.linalg.solve(a, b)
    pi = np.maximum(pi, 0)  # Она убирает возможные маленькие отрицательные значения из-за вычислительной погрешности
    pi = pi / np.sum(pi)    # и нормирует сумму вероятностей к 1
    return pi


def choose_by_probabilities(probabilities):
    """Выбор номера состояния по ряду распределения."""
    alpha = np.random.random() # случайное число от 0 до 1.
    cumulative = 0.0

    for index, p in enumerate(probabilities):
        cumulative += p
        if alpha <= cumulative:
            return index

    return len(probabilities) - 1  # probabilities = [0.2, 0.5, 0.3], 0.0–0.2 → первое, 0.2–0.7 → второе, 0.7–1.0 → третье, alpha = 0.63, выбирается второе состояние


def simulate_ctmc(q, total_time):
    """Моделирует цепь Маркова с непрерывным временем на интервале [0; total_time]."""
    n = q.shape[0]
    p = transition_probability_matrix(q)
    pi = stationary_distribution(q)

    current_state = choose_by_probabilities(pi) # Начальное состояние выбирается случайно по стационарному распределению
    t = 0.0
    durations = np.zeros(n)
    segments = []

    while t < total_time: # как моделируется один шаг
        exit_rate = -q[current_state, current_state]
        stay_time = expon.rvs(scale=1 / exit_rate)  # генерируется случайное время пребывания: сколько дней погода будет оставаться в текущем состоянии до следующего перехода

        end_t = min(t + stay_time, total_time)
        real_duration = end_t - t
        durations[current_state] += real_duration
        segments.append((t, end_t, current_state))

        t = end_t
        if t >= total_time:
            break

        current_state = choose_by_probabilities(p[current_state]) # выбирается следующее состояние. смотрит на строку матрицы вероятностей и случайно выбирает, куда перейти дальше.

    empirical = durations / total_time                            # Ясно: 130/365 = 0.356 Облачно: 150/365 = 0.411 Пасмурно: 85/365 = 0.233
    return segments, empirical, pi, p, durations                  # история смены погоды; эмп вер; теор вер; матрица вер пер; вр пребывания.


class WeatherMarkovApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная 7 — моделирование погоды")
        self.resize(1300, 800)
        self.setStyleSheet(STYLE)

        self.q = None
        self.p = None
        self.pi = None
        self.empirical = None
        self.durations = None
        self.segments = []
        self.visible_segments_count = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.show_next_segment)

        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(10, 10, 10, 10)
        left_panel.setSpacing(10)

        title = QLabel("Матрица интенсивностей переходов")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_panel.addWidget(title)

        hint = QLabel("Заполняются только переходы i → j. Диагональ считается автоматически.")
        hint.setWordWrap(True)
        left_panel.addWidget(hint)

        self.rate_table = QTableWidget(3, 3)
        self.rate_table.setHorizontalHeaderLabels(STATE_NAMES)
        self.rate_table.setVerticalHeaderLabels(STATE_NAMES)
        self.rate_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rate_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_panel.addWidget(self.rate_table)
        self.fill_default_rates()

        left_panel.addWidget(QLabel("Время моделирования, дней:"))
        self.time_box = QDoubleSpinBox()
        self.time_box.setRange(1, 100000)
        self.time_box.setValue(365)
        self.time_box.setDecimals(2)
        left_panel.addWidget(self.time_box)

        left_panel.addWidget(QLabel("Скорость анимации, мс на переход:"))
        self.speed_box = QDoubleSpinBox()
        self.speed_box.setRange(10, 2000)
        self.speed_box.setValue(500)
        self.speed_box.setDecimals(0)
        left_panel.addWidget(self.speed_box)

        self.btn_run = QPushButton("Запустить моделирование")
        self.btn_run.clicked.connect(self.run_simulation)
        left_panel.addWidget(self.btn_run)

        self.btn_export = QPushButton("Сохранить результаты в CSV")
        self.btn_export.clicked.connect(self.export_csv)
        left_panel.addWidget(self.btn_export)

        self.card_q = StatCard("Матрица Q (интенсивности переходов)")
        self.card_p = StatCard("Матрица P (вероятностей переходов)")
        self.card_pi = StatCard("Теоретические вероятности (доля времени)")
        left_panel.addWidget(self.card_q)
        left_panel.addWidget(self.card_p)
        left_panel.addWidget(self.card_pi)
        left_panel.addStretch()

        right_panel = QVBoxLayout()

        self.fig = Figure(figsize=(8, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        right_panel.addWidget(self.canvas, 3)

        self.stats_table = QTableWidget(3, 5)
        self.stats_table.setHorizontalHeaderLabels([
            "Состояние", "Время пребывания", "Эмпирическая P", "Теоретическая P", "Абс. ошибка"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_panel.addWidget(self.stats_table, 1)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

    def fill_default_rates(self):
        defaults = [
            [0.0, 0.35, 0.15],
            [0.25, 0.0, 0.30],
            [0.20, 0.40, 0.0],
        ]

        for i in range(3):
            for j in range(3):
                item = QTableWidgetItem("—" if i == j else str(defaults[i][j]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if i == j:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled) # делаются не редактируемыми
                    item.setBackground(Qt.GlobalColor.lightGray)

                self.rate_table.setItem(i, j, item)

    def read_rates(self):
        rates = np.zeros((3, 3), dtype=float)

        for i in range(3):
            for j in range(3):
                if i == j:
                    continue

                item = self.rate_table.item(i, j)
                if item is None or not item.text().strip():
                    raise ValueError(f"Не задана интенсивность q{i + 1}{j + 1}.")

                text = item.text().replace(",", ".")
                rates[i, j] = float(text)

        return rates

    def run_simulation(self):
        try:
            self.timer.stop()

            rates = self.read_rates()
            total_time = self.time_box.value()

            self.q = build_generator_matrix(rates)
            self.p = transition_probability_matrix(self.q)
            self.segments, self.empirical, self.pi, self.p, self.durations = simulate_ctmc(self.q, total_time)

            self.visible_segments_count = 0
            self.update_text_blocks()
            self.update_stats_table()
            self.draw_plots(animated=True)

            interval = int(self.speed_box.value())
            self.timer.start(interval)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def show_next_segment(self):
        if self.visible_segments_count < len(self.segments):
            self.visible_segments_count += 1
            self.draw_plots(animated=True)
        else:
            self.timer.stop()

    def update_text_blocks(self):
        self.card_q.set_text(self.format_matrix(self.q))
        self.card_p.set_text(self.format_matrix(self.p))
        self.card_pi.set_text(self.format_vector(self.pi))

    def update_stats_table(self):
        for i in range(3):
            error = abs(self.empirical[i] - self.pi[i])
            row = [
                f"{STATE_NUMBERS[i]} — {STATE_NAMES[i]}",
                f"{self.durations[i]:.4f}",
                f"{self.empirical[i]:.4f}",
                f"{self.pi[i]:.4f}",
                f"{error:.4f}",
            ]
            for col, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stats_table.setItem(i, col, item)

    def draw_plots(self, animated=False):
        self.fig.clear()

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax2 = self.fig.add_subplot(2, 1, 2)

        shown = self.segments[:self.visible_segments_count] if animated else self.segments

        for start, end, state in shown:
            ax1.hlines(STATE_NUMBERS[state], start, end, linewidth=4, color="#2ecc71")
            ax1.vlines(end, 0.8, 3.2, alpha=0.15, color="#2ecc71")

        ax1.set_title("Смена погоды во времени")
        ax1.set_xlabel("Время, дни")
        ax1.set_ylabel("Состояние")
        ax1.set_yticks(STATE_NUMBERS)
        ax1.set_yticklabels([f"{i} — {name}" for i, name in zip(STATE_NUMBERS, STATE_NAMES)])
        ax1.set_ylim(0.7, 3.3)
        ax1.grid(alpha=0.3)

        x = np.arange(3)
        width = 0.35
        ax2.bar(
            x - width / 2,
            self.pi,
            width=width,
            label="Теоретические",
            color="#2ecc71"
        )

        ax2.bar(
            x + width / 2,
            self.empirical,
            width=width,
            label="Эмпирические",
            color="#f1c40f"
        )
        ax2.set_title("Сравнение стационарных вероятностей")
        ax2.set_ylabel("Вероятность")
        ax2.set_ylim(0, 1)
        ax2.set_xticks(x)
        ax2.set_xticklabels(STATE_NAMES)
        ax2.grid(axis="y", alpha=0.3)
        ax2.legend()

        self.canvas.draw()

    def export_csv(self):
        if self.empirical is None:
            QMessageBox.warning(self, "Нет данных", "Сначала запустите моделирование.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV",
            "weather_markov_results.csv",
            "CSV files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")

                writer.writerow(["Матрица интенсивностей Q"])
                for row in self.q:
                    writer.writerow([f"{value:.6f}" for value in row])

                writer.writerow([])
                writer.writerow(["Матрица вероятностей переходов P"])
                for row in self.p:
                    writer.writerow([f"{value:.6f}" for value in row])

                writer.writerow([])
                writer.writerow(["Состояние", "Время пребывания", "Эмпирическая P", "Теоретическая P", "Абс. ошибка"])
                for i in range(3):
                    writer.writerow([
                        STATE_NAMES[i],
                        f"{self.durations[i]:.6f}",
                        f"{self.empirical[i]:.6f}",
                        f"{self.pi[i]:.6f}",
                        f"{abs(self.empirical[i] - self.pi[i]):.6f}",
                    ])

                writer.writerow([])
                writer.writerow(["История моделирования"])
                writer.writerow(["Начало", "Конец", "Состояние"])
                for start, end, state in self.segments:
                    writer.writerow([f"{start:.6f}", f"{end:.6f}", STATE_NAMES[state]])

            QMessageBox.information(self, "Готово", "Результаты сохранены в CSV-файл.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))

    @staticmethod
    def format_matrix(matrix):
        lines = []
        for row in matrix:
            lines.append("  ".join(f"{value:8.4f}" for value in row))
        return "\n".join(lines)

    @staticmethod
    def format_vector(vector):
        lines = []
        for name, value in zip(STATE_NAMES, vector):
            lines.append(f"{name}: {value:.4f}")
        return "\n".join(lines)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherMarkovApp()
    window.show()
    sys.exit(app.exec())
