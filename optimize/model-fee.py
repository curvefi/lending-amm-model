from libmodel import get_loss_rate

if __name__ == '__main__':
    import pylab
    import numpy as np

    A = 35
    fees = np.logspace(np.log10(0.0001), np.log10(0.02), 100)
    losses = []
    for fee in fees:
        losses.append(get_loss_rate(A, fee))
        print(fee, losses[-1])

    pylab.semilogx(fees, losses)
    pylab.show()
