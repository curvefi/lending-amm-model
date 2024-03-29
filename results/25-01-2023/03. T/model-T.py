from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.085
    fee = 0.006
    days = 1
    samples = 20000
    n_top_samples = 20
    # n_top_samples = samples
    T = np.logspace(np.log10(100), np.log10(50000), 40)
    losses = []
    for t in T:
        losses.append(
            get_loss_rate(
                range_size, fee, Texp=float(t), measure='xtopmax2',
                min_loan_duration=days, max_loan_duration=days, samples=samples,
                n_top_samples=n_top_samples))
        print(t, losses[-1])

    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogx(T, losses)
        pylab.xlabel('T (s)')
        pylab.ylabel(f'Worst loss in {days} days')
        pylab.show()
    except ImportError:
        pass
