#!/usr/bin/env python3

import pylab
import numpy as np
from libsimulate import get_loss_shift

# RANGE_SIZE = 0.2
TEXP = 10000
LOAN_DURATION = 3  # days
SAMPLES = 50000
FEE = 0.01

for range_size in [0.2, 0.05]:
    results, shifts = get_loss_shift(range_size, FEE, Texp=TEXP, min_loan_duration=LOAN_DURATION, max_loan_duration=LOAN_DURATION, samples=SAMPLES)

    results = np.array(results)
    shifts = np.array(shifts)

    bins = np.linspace(-0.4, max(shifts), 40)
    db = bins[1] - bins[0]

    xshifts = [100 * shifts[(shifts >= s) * (shifts < s + db)].mean() for s in bins]
    xloss = [100 * results[(shifts >= s) * (shifts < s + db)].mean() for s in bins]

    pylab.plot(xshifts, xloss, label='range_size={0:.2f}'.format(range_size))

pylab.xlabel('Price drop relative to liquidation threshold [%]')
pylab.ylabel('Relative loss [%]')
pylab.title('Losses during a dip')
pylab.legend()
pylab.grid()
pylab.show()
