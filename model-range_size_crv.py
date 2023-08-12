from libsimulate_crv import get_loss_rate, A

if __name__ == '__main__':
    import numpy as np

    try:
        import matplotlib
        import matplotlib.ticker
        import sys
        if 'PyPy' not in sys.version:
            matplotlib.use('Qt5Agg')
        else:
            matplotlib.use('TkAgg')
        from matplotlib import pyplot as plt

    except ImportError:
        raise

    print('Amplification:', A)

    # range_size = np.linspace(0.01, 0.61, 21) - 0.00001
    range_size = np.array([0.05, 0.1, 0.3, 0.6, 0.8]) - 0.00001
    fee = 0.01
    duration = 0.3
    samples = 100000
    losses = []
    combined_losses = []
    for r in range_size:
        r = float(r)
        losses.append(get_loss_rate(r, fee, Texp=600, measure='xtopmax2', min_loan_duration=duration, max_loan_duration=duration,
                                    samples=samples, n_top_samples=20,
                                    other={'dynamic_fee_multiplier': 0.0, 'use_po_fee': 1, 'po_fee_delay': 1}))
        cl = 1 - (1 - losses[-1]) * (1 - r)**0.5
        combined_losses.append(cl)
        print(r, losses[-1], cl)

    xticks = np.array([1, 2, 3, 5, 10, 20, 30, 50, 60])
    xticks = xticks[(xticks >= range_size.min() * 100) * (xticks <= range_size.max() * 100)]

    fig, ax = plt.subplots()
    ax.plot(range_size * A, losses, label='Loss')
    ax.plot(range_size * A, combined_losses, label='Autoliquidation value loss')

    ax.set_xscale('log')
    ax.set_xticks(xticks)
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

    ax.set_xlabel('Range size')
    ax.set_ylabel('Loss')
    ax.grid()
    ax.legend()
    plt.show()
