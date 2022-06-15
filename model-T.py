from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.2
    fee = 0.01
    days = 7
    samples = 20000
    T = np.logspace(np.log10(500), np.log10(100000), 40)
    losses = []
    for t in T:
        losses.append(
            get_loss_rate(
                range_size, fee, Texp=float(t), measure='xtopmax2',
                min_loan_duration=days, max_loan_duration=days, samples=samples))
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
