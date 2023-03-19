from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.03999
    fee = 0.003
    days = 0.3
    samples = 100000
    n_top_samples = 20
    # n_top_samples = samples
    T = np.logspace(np.log10(300), np.log10(5000), 30)
    losses = []
    for t in T:
        losses.append(
            get_loss_rate(
                range_size, fee, Texp=float(t), measure='xtopmax2',
                min_loan_duration=days, max_loan_duration=days, samples=samples,
                n_top_samples=n_top_samples, other={'dynamic_fee_multiplier': 0, 'use_po_fee': 1, 'po_fee_delay': 2}))
        print(t, losses[-1])

    try:
        import sys
        if 'PyPy' not in sys.version:
            import matplotlib
            matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogx(T, losses)
        pylab.xlabel('T (s)')
        pylab.ylabel(f'Worst loss in {days} days')
        pylab.show()
    except ImportError:
        pass
