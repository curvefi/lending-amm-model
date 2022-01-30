from libsimulate_crv import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = np.logspace(np.log10(0.05), np.log10(0.65), 30)
    fee = 0.01
    losses = []
    for r in range_size:
        r = float(r)
        losses.append(get_loss_rate(r, fee, Texp=10000, measure='xtopmax2', min_loan_duration=3, max_loan_duration=3, samples=1000))
        print(r, losses[-1])

    try:
        import matplotlib
        matplotlib.use('tkagg')
        import pylab
        pylab.semilogx(range_size, losses)
        pylab.show()
    except ImportError:
        pass
