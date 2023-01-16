from libsimulate import get_loss_rate

if __name__ == '__main__':
    import numpy as np

    range_size = np.logspace(np.log10(0.03), np.log10(0.65), 40)
    fee = 0.003
    losses = []
    combined_losses = []
    for r in range_size:
        r = float(r)
        losses.append(get_loss_rate(r, fee, Texp=600, measure='xtopmax2', min_loan_duration=1, max_loan_duration=1,
                                    samples=20000, n_top_samples=20))
        cl = (1 - (1 - r)**0.5) + losses[-1]
        combined_losses.append(cl)
        print(r, losses[-1], cl)

    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
        import pylab
        pylab.semilogx(range_size, losses, label='Loss')
        pylab.semilogx(range_size, combined_losses, label='Autoliquidation value loss')
        pylab.xlabel('Range size')
        pylab.ylabel('Loss')
        pylab.legend()
        pylab.show()
    except ImportError:
        pass
