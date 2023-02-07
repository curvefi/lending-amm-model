#!/usr/bin/env python3
# Plot get_y_down vs balnce to evaluate continuity of the functions get_x_down / get_y_up

import pylab
import matplotlib
import numpy as np
from libmodel import LendingAMM

matplotlib.use('Qt5Agg')

if __name__ == '__main__':
    for A in [100, 10]:
        p = 3000
        amm = LendingAMM(p, A)

        # We change linearly because it doesn't even matter what happens in the middle - we care about edges here

        x = np.linspace(0, 1, 100)
        y = []

        for f in x:
            amm.bands_x[0] = int(p * f * 1e18)
            amm.bands_y[0] = int((1 - f) * 1e18)
            # y.append(amm.get_x_down(0))
            y.append(amm.get_y_up(0))

        y = np.array(y)

        assert x[0] == 0
        assert 1 - x[-1] == 0

        pylab.plot(x, y / 1e18)
    pylab.show()
