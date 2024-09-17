import numpy as np
import matplotlib.pyplot as plt

from GBN import GBN_transmisser


def count_props():
    probabilities = [0.0, 0.1, 0.2]#np.linspace(0.0, 0.90, 10)
    window_size = 2
    timeout = 0.2
    max_number = 10
    repeats = 4

    simulations = [
        {
            "NAME" : "Go-back N",
            "FUNC" : GBN_transmisser.make_simulation
        },
        {
            "NAME" : "GBN",
            "FUNC" : GBN_transmisser.make_simulation
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
    for sim in simulations:
        k_arr, times_arr = [], []
        for i, p in enumerate(probabilities):
            ks[sim["NAME"]][i] = np.mean(ks[sim["NAME"]][i])
            times[sim["NAME"]][i] = np.mean(times[sim["NAME"]][i])
            k_arr.append(ks[sim["NAME"]][i])
            times_arr.append(times[sim["NAME"]][i])
        
        axes[0].plot(probabilities, k_arr, label=sim["NAME"])
        axes[1].plot(probabilities, times_arr, label=sim["NAME"])
        
    axes[0].set_xlabel('Вероятность потери пакета')
    axes[0].set_ylabel('Коэффициент эффективности')
    axes[0].legend()

    axes[1].set_xlabel('Вероятность потери пакета')
    axes[1].set_ylabel('Время передачи пакета (с)')
    axes[1].legend()
    
    fig.savefig("./../res/prob_test.png")

if __name__ == "__main__":
    count_props()