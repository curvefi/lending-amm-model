from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.08
    fee = 0.006
    T = 600
    samples = 1000
    losses = []
    max_losses = []

    durations = np.logspace(np.log10(0.2), np.log10(30), 20)

    for d in durations:
        losses.append(get_loss_rate(range_size, fee, Texp=T, measure='xavg', min_loan_duration=d, max_loan_duration=d,
                                    samples=1000, n_top_samples=20))
        max_losses.append(get_loss_rate(range_size, fee, Texp=T, measure='xtopmax2', min_loan_duration=d, max_loan_duration=d,
                                        samples=10000, n_top_samples=20))
        print(d, losses[-1], max_losses[-1])

    try:
        import matplotlib
        import matplotlib.ticker
        matplotlib.use('Qt5Agg')
        from matplotlib import pyplot as plt

        xticks = np.array([0.1, 0.2, 0.3, 0.5, 1, 2, 3, 5, 10, 20, 30, 50])
        yticks = np.array([0.001, 0.002, 0.003, 0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 0.30, 0.50])
        xticks = xticks[(xticks >= durations.min()) * (xticks <= durations.max())]
        yticks = yticks[(yticks >= min(losses)) * (yticks <= max(max_losses))]

        fig, ax = plt.subplots()
        ax.plot(durations, losses, label='Avg loss')
        ax.plot(durations, max_losses, label='Max loss')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.grid()
        ax.set_xlabel('t (days)')
        ax.set_ylabel('Loss')
        ax.set_title('Loss vs time when borrowed right at liquidation limit')
        plt.legend()
        plt.show()
    except ImportError:
        pass
