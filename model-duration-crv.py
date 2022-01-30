from libsimulate_crv import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    duration = np.logspace(np.log10(1), np.log10(50), 30)
    range_size = 0.25
    fee = 0.01
    losses = []
    for d in duration:
        d = float(d)
        losses.append(get_loss_rate(range_size, fee, Texp=10000, measure='xavg', min_loan_duration=d, max_loan_duration=d, samples=2000))
        print(d, losses[-1])

    try:
        import matplotlib
        matplotlib.use('tkagg')
        import pylab
        pylab.loglog(duration, losses)
        pylab.show()
    except ImportError:
        pass
