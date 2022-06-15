#!/usr/bin/env python3

import matplotlib
import pylab
import numpy as np
from libsimulate import get_loss_shift

# TEXP = 10000
LOAN_DURATION = 3  # days
SAMPLES = 50000
FEE = 0.01
MIN_RANGE = -0.2
N_BINS = 30
RANGE_SIZE = 0.2

matplotlib.use('tkagg')

for texp in [1000, 5000, 10000, 30000, 50000, 100000]:
    results, shifts = get_loss_shift(RANGE_SIZE, FEE, Texp=texp, min_loan_duration=LOAN_DURATION, max_loan_duration=LOAN_DURATION, samples=SAMPLES)

    results = np.array(results)
    shifts = np.array(shifts)

    bins = np.linspace(MIN_RANGE, max(shifts), N_BINS)
    db = bins[1] - bins[0]

    xshifts = [100 * shifts[(shifts >= s) * (shifts < s + db)].mean() for s in bins]
    xloss = [100 * results[(shifts >= s) * (shifts < s + db)].mean() for s in bins]

    print(texp)
    pylab.plot(xshifts, xloss, label='Texp={0}'.format(texp))

pylab.xlabel('Price drop relative to liquidation threshold [%]')
pylab.ylabel('Relative loss [%]')
pylab.title('Losses during a dip')
pylab.legend()
pylab.grid()
pylab.show()
