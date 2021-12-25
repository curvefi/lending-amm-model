from libmodel import get_loss_rate

if __name__ == '__main__':
    import pylab
    import numpy as np

    A = np.logspace(np.log10(5), np.log10(150), 20)
    fee = 0.003
    losses = []
    for a in A:
        losses.append(get_loss_rate(a, fee))
        print(a, losses[-1])

    pylab.semilogx(A, losses)
    pylab.show()
