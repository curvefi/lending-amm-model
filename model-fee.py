from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.2
    T = 600
    measure = 'xtopmax2'
    fee = np.logspace(np.log10(0.0003), np.log10(0.05), 30)
    losses = []
    for f in fee:
        f = float(f)
        losses.append(get_loss_rate(range_size, f, Texp=T, measure=measure, min_loan_duration=1, max_loan_duration=1,
                                    samples=20000, n_top_samples=20))
        print(f, losses[-1])

    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogx(fee, losses)
        pylab.xlabel('Fee')
        pylab.ylabel('Loss')
        pylab.show()
    except ImportError:
        pass
