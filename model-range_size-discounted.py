from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = np.logspace(np.log10(0.05), np.log10(0.25), 8)
    fee = 0.01
    samples = 2000
    measure = 'xtopmax2'
    duration = 7
    Texp = 7000
    losses = []
    for r in range_size:
        r = float(r)
        eff_loss = get_loss_rate(
            r, fee, Texp=Texp, measure=measure,
            min_loan_duration=duration, max_loan_duration=duration,
            samples=samples)
        eff_loss += 1 - (1 - r)**0.5
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
