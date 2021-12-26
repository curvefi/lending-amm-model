from libmodel import get_loss_rate

if __name__ == '__main__':
    import pylab
    import numpy as np

    T = np.logspace(np.log10(30), np.log10(12000), 50)
    fee = 0.001
    A = 35
    losses = []
    for t in T:
        losses.append(get_loss_rate(A, fee, t, measure="avg"))
        print(t, losses[-1])

    pylab.semilogx(T, losses)
    pylab.show()
