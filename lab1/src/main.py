import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from GBN import GBN_transmisser
from SR import SR_transmisser


def count_props():
    probabilities = np.linspace(0.0, 0.90, 10)
    window_size = 7
    timeout = 0.2
    max_number = 100
    repeats = 5

    simulations = [
        {
             "NAME" : "Go-back N",
             "FUNC" : GBN_transmisser.make_simulation
        },
        {
            "NAME" : "Selective repeat",
            "FUNC" : SR_transmisser.make_simulation
        }
    ]

    ks, times = {}, {}
    for _ in range(repeats):
        for sim in simulations:
            if sim["NAME"] not in ks:
                ks[sim["NAME"]] = {}

            if sim["NAME"] not in times:
                times[sim["NAME"]] = {}
            
            for i, p in enumerate(probabilities):
                if i not in ks[sim["NAME"]]:
                    ks[sim['NAME']][i] = []
                if i not in times[sim["NAME"]]:
                    times[sim['NAME']][i] = []

                received_msgs, posted_msgs, k, elapsed_time = sim["FUNC"](max_number, window_size, timeout, p)
                print(f"Prop={float(p)}, sim={sim['NAME']}, Effecienty={k}, time={elapsed_time}")
                
                ks[sim['NAME']][i].append(k)
                times[sim['NAME']][i].append(elapsed_time)

    fig, axes = plt.subplots(1, 2, figsize=(22,8))
    data = {}
    for sim in simulations:
        k_arr, times_arr = [], []
        for i, p in enumerate(probabilities):
            ks[sim["NAME"]][i] = np.mean(ks[sim["NAME"]][i])
            times[sim["NAME"]][i] = np.mean(times[sim["NAME"]][i])
            k_arr.append(ks[sim["NAME"]][i])
            times_arr.append(times[sim["NAME"]][i])
        
        data[sim["NAME"] + "_k"] = k_arr
        data[sim["NAME"] + "_times"] = times_arr

        axes[0].plot(probabilities, k_arr, label=sim["NAME"])
        axes[1].plot(probabilities, times_arr, label=sim["NAME"])
        
    axes[0].set_xlabel('Вероятность потери 1-го пакета')
    axes[0].set_ylabel('Коэффициент эффективности')
    axes[0].legend()
    axes[0].grid()

    axes[1].set_xlabel('Вероятность потери 1-го пакета')
    axes[1].set_ylabel('Время передачи пакетов (сек)')
    axes[1].legend()
    axes[1].grid()

    fig.savefig("./../res/prob_test.png")
    pd.DataFrame.from_dict(data).to_csv("./../res/probs_values.csv")

def count_win_sizes():
    probability = 0.3
    window_sizes = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    timeout = 0.2
    max_number = 100
    repeats = 30

    simulations = [
        {
             "NAME" : "Go-back N",
             "FUNC" : GBN_transmisser.make_simulation
        },
        {
            "NAME" : "Selective repeat",
            "FUNC" : SR_transmisser.make_simulation
        }
    ]

    ks, times = {}, {}
    for _ in range(repeats):
        for sim in simulations:
            if sim["NAME"] not in ks:
                ks[sim["NAME"]] = {}

            if sim["NAME"] not in times:
                times[sim["NAME"]] = {}
            
            for i, ws in enumerate(window_sizes):
                if i not in ks[sim["NAME"]]:
                    ks[sim['NAME']][i] = []
                if i not in times[sim["NAME"]]:
                    times[sim['NAME']][i] = []

                received_msgs, posted_msgs, k, elapsed_time = sim["FUNC"](max_number, ws, timeout, probability)
                print(f"Win_size={ws}, sim={sim['NAME']}, Effecienty={k}, time={elapsed_time}")
                
                ks[sim['NAME']][i].append(k)
                times[sim['NAME']][i].append(elapsed_time)

    fig, axes = plt.subplots(1, 2, figsize=(22,8))
    data = {}
    for sim in simulations:
        k_arr, times_arr = [], []
        for i, ws in enumerate(window_sizes):
            ks[sim["NAME"]][i] = np.mean(ks[sim["NAME"]][i])
            times[sim["NAME"]][i] = np.mean(times[sim["NAME"]][i])
            k_arr.append(ks[sim["NAME"]][i])
            times_arr.append(times[sim["NAME"]][i])
        
        data[sim["NAME"] + "_k"] = k_arr
        data[sim["NAME"] + "_times"] = times_arr

        axes[0].plot(window_sizes, k_arr, label=sim["NAME"])
        axes[1].plot(window_sizes, times_arr, label=sim["NAME"])
        
    axes[0].set_xlabel('Размер окна')
    axes[0].set_ylabel('Коэффициент эффективности')
    axes[0].legend()
    axes[0].grid()

    axes[1].set_xlabel('Размер окна')
    axes[1].set_ylabel('Время передачи пакетов (сек)')
    axes[1].legend()
    axes[1].grid()

    fig.savefig("./../res/ws_test.png")
    pd.DataFrame.from_dict(data).to_csv("./../res/ws_values.csv")

if __name__ == "__main__":
    count_win_sizes()
    count_props()
