from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = np.logspace(np.log10(0.05), np.log10(0.3), 20)
    fee = 0.01
    samples = 10000
    measure = 'realdiff'
    duration = 7
    Texp = 7000
    losses = []
    for r in range_size:
        r = float(r)
        eff_loss = get_loss_rate(
            r, fee, Texp=Texp, measure=measure,
            min_loan_duration=duration, max_loan_duration=duration,
            samples=samples)
        losses.append(eff_loss)
        print(r, eff_loss)

    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogx(range_size, losses)
        pylab.xlabel('Range size')
        pylab.ylabel('max(real_loss - health_loss)')
        pylab.grid()
        pylab.show()
    except ImportError:
        pass
