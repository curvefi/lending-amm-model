from libmodel import get_loss_rate

if __name__ == '__main__':
    import pylab
    import numpy as np

    A = np.logspace(np.log10(2), np.log10(100), 20)
    fee = 0.0014
    losses = []
    for a in A:
        losses.append(get_loss_rate(a, fee))
        print(a, losses[-1])

    pylab.plot(A, losses)
    pylab.show()
