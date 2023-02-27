from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = 0.1
    T = 600
    measure = 'xtopmax2'
    fee = 0.00
    muls = np.linspace(0, 1.99, 20)
    losses = []
    for mul in muls:
        mul = float(mul)
        losses.append(get_loss_rate(range_size, fee, Texp=T, measure=measure, min_loan_duration=1, max_loan_duration=1,
                                    samples=20_000, n_top_samples=20,
                                    other={'dynamic_fee_multiplier': mul, 'use_po_fee': 1, 'po_fee_delay': 1}))
        print(mul, losses[-1])

    try:
        import sys
        if 'PyPy' not in sys.version:
            import matplotlib
            matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogy(muls, losses)
        pylab.xlabel('Mul')
        pylab.ylabel('Loss')
        pylab.show()
    except ImportError:
        pass
