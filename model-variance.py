#!/usr/bin/env python3

import matplotlib
import pylab
import numpy as np
from libsimulate import get_loss_variance

# TEXP = 10000
LOAN_DURATION = 3  # days
SAMPLES = 100000
FEE = 0.01
N_BINS = 30
RANGE_SIZE = 0.2

matplotlib.use('tkagg')

# for texp in [1000, 5000, 10000, 30000, 50000, 100000]:
texp = 600
results, variance = get_loss_variance(RANGE_SIZE, FEE, Texp=texp, min_loan_duration=LOAN_DURATION, max_loan_duration=LOAN_DURATION, samples=SAMPLES)

results = np.array(results)
variances = np.array(variance)

bins = np.linspace(0, max(variances), N_BINS)
db = bins[1] - bins[0]

xvariances = [100 * variances[(variances >= s) * (variances < s + db)].mean() for s in bins]
xloss = [100 * results[(variances >= s) * (variances < s + db)].mean() for s in bins]

for i in range(N_BINS):
    print(i, bins[i], len(variances[(variances >= bins[i]) * (variances < bins[i] + db)]))
print(texp)
pylab.plot(xvariances, xloss, label='Texp={0}'.format(texp))

pylab.xlabel('Price variance [%] (sqrt(D) / M)')
pylab.ylabel('Relative loss [%]')
pylab.title('Losses during a dip')
pylab.legend()
pylab.grid()
pylab.show()
