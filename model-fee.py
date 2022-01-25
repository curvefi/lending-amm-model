from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.1
    fee = np.logspace(np.log10(0.0003), np.log10(0.3), 7)
    losses = []
    for f in fee:
        f = float(f)
        losses.append(get_loss_rate(range_size, f, Texp=10000, measure='xavg', min_loan_duration=30, max_loan_duration=30, samples=500))
        print(f, losses[-1])

    try:
        import matplotlib
        matplotlib.use('tkagg')
        import pylab
        pylab.semilogx(fee, losses)
        pylab.show()
    except ImportError:
        pass
