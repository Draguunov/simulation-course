import numpy as np
from numba import jit
import time

@jit(nopython=True)
def simulate(rho, c, lam, Ta, Tn, T0, L, h, total_time, tau):
    # разбиваем на отрезки
    Nx = int(round(L / h))
    if Nx < 2: Nx = 2
    h = L / Nx

    # сколько раз нужно обновить поле температуры
    steps_n = int(round(total_time / tau))
    if steps_n < 1: steps_n = 1

    # начальное распределение температуры
    T = np.full(Nx + 1, float(T0))
    T[0] = float(Ta)
    T[Nx] = float(Tn)

    #коэф. для расчёта
    A_i = lam / h ** 2
    C_i = A_i
    B_i = (2 * lam / h ** 2) + (rho * c / tau)

    # Метод прогонки TDMA
    alpha = np.zeros(Nx + 1)
    beta = np.zeros(Nx + 1)

    for n in range(steps_n):
        alpha[0] = 0.0
        beta[0] = float(Ta)

        # прямой проход
        for i in range(1, Nx):
            F_i = -(rho * c / tau) * T[i]

            denom = B_i - C_i * alpha[i - 1]

            alpha[i] = A_i / denom
            beta[i] = (C_i * beta[i - 1] - F_i) / denom

        # обратный проход
        T_next = np.empty(Nx + 1)
        T_next[Nx] = float(Tn)
        T_next[0] = float(Ta)

        for i in range(Nx - 1, 0, -1):
            T_next[i] = alpha[i] * T_next[i + 1] + beta[i]

        T = T_next
    # температура в центре стержня
    return T[Nx // 2]
def get_float(prompt, default):
    """Запрашивает число, при пустом вводе возвращает значение по умолчанию."""
    val = input(f"{prompt} [{default}]: ").strip()
    if val == "":
        return default
    return float(val)
def table_run():
    """Построение таблицы зависимости от шагов ."""
    print("\n--- Параметры материала ---")
    rho = get_float("Плотность (кг/м³)", 8960.0)
    c = get_float("Теплоёмкость (Дж/(кг·К))", 385.0)
    lam = get_float("Теплопроводность (Вт/(м·К))", 401.0)
    L = get_float("Длина стержня (м)", 0.1)

    print("\n--- Температуры (°C) ---")
    T0 = get_float("Начальная температура", 20.0)
    Ta = get_float("Температура слева", 190.0)
    Tn = get_float("Температура справа", 30.0)

    # Фиксированные значения времени моделирования
    total_time = 2.0

    dts = [0.1, 0.01, 0.001, 0.0001]
    hs = [0.1, 0.01, 0.001, 0.0001]

    print("\nТаблица температур в центре (°C):")
    print("dt \\ h   " + "".join(f"{h:>8}" for h in hs))
    for dt in dts:
        row = [f"{dt:<8}"]
        for h in hs:
            try:
                center = simulate(rho, c, lam, Ta, Tn, T0, L, h, total_time, dt)
                row.append(f"{center:8.2f}")
            except Exception:
                row.append("     —   ") # если расчёт не удался, н-р слишком мелкий шаг
        print("".join(row))

    print("\nТаблица времени расчёта (с):")
    print("dt \\ h   " + "".join(f"{h:>8}" for h in hs))
    for dt in dts:
        row = [f"{dt:<8}"]
        for h in hs:
            try:
                start = time.perf_counter()
                simulate(rho, c, lam, Ta, Tn, T0, L, h, total_time, dt)
                elapsed = time.perf_counter() - start
                row.append(f"{elapsed:8.4f}")
            except Exception:
                row.append("     —   ")
        print("".join(row))
def main():
    print("Моделирование теплопроводности. Таблица зависимости от шагов")
    table_run()

if __name__ == "__main__":
    main()

