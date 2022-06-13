from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = np.logspace(np.log10(0.05), np.log10(0.25), 30)
    fee = 0.003
    losses = []
    for r in range_size:
        r = float(r)
        eff_loss = get_loss_rate(r, fee, Texp=10000, measure='xtopmax2', min_loan_duration=30, max_loan_duration=30, samples=1000)
        eff_loss += 1 - (1 - r)**0.5
        # xavg?
        losses.append(eff_loss)
        print(r, eff_loss)

    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogx(range_size, losses)
        pylab.xlabel('Range size')
        pylab.ylabel('Discounted loss')
        pylab.show()
    except ImportError:
        pass
