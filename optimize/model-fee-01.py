from libmodel import get_loss_rate

if __name__ == '__main__':
    import pylab
    import numpy as np

    A = 22
    fees = np.logspace(np.log10(0.00005), np.log10(0.01), 20)
    losses = []
    for fee in fees:
        losses.append(get_loss_rate(A, fee))
        print(fee, losses[-1])

    pylab.plot(fees, losses)
    pylab.show()
