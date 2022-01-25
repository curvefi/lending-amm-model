from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.1
    T = np.logspace(np.log10(200), np.log10(100000), 20)
    losses = []
    for t in T:
        losses.append(get_loss_rate(range_size, 0.003, Texp=float(t), measure='topmax', min_loan_duration=30, max_loan_duration=30, samples=500))
        print(t, losses[-1])

    try:
        import matplotlib
        matplotlib.use('tkagg')
        import pylab
        pylab.semilogx(T, losses)
        pylab.show()
    except ImportError:
        pass
