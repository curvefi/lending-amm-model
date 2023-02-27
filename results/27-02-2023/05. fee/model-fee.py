from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.039999
    T = 600
    measure = 'xtopmax2'
    fee = np.logspace(np.log10(0.001), np.log10(0.015), 20)
    losses = []
    for f in fee:
        f = float(f)
        losses.append(get_loss_rate(range_size, f, Texp=T, measure=measure, min_loan_duration=.3, max_loan_duration=.3,
                                    samples=200_000, n_top_samples=20,
                                    other={'dynamic_fee_multiplier': 0, 'use_po_fee': 1, 'po_fee_delay': 1}))
        print(f, losses[-1])

    try:
        import sys
        if 'PyPy' not in sys.version:
            import matplotlib
            matplotlib.use('Qt5Agg')
        import pylab
        pylab.plot(fee, losses)
        pylab.xlabel('Fee')
        pylab.ylabel('Loss')
        pylab.show()
    except ImportError:
        pass
