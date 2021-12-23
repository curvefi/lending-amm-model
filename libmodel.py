import json
import gzip
import random
from multiprocessing import Pool, cpu_count
from datetime import datetime
from math import sqrt


MIN_LOAN_DURATION = 1  # day
MAX_LOAN_DURATION = 14  # days
EXT_FEE = 0.0005
SAMPLES = 4000
T = 600  # s


def load_prices(f, add_reverse=True):
    with gzip.open(f, "r") as f:
        data = json.load(f)
    # timestamp, OHLC, vol
    data = [[int(d[0])] + [float(x) for x in d[1:6]] for d in data]
    if add_reverse:
        t0 = data[-1][0]
        data += [[t0 + (t0 - d[0])] + d[1:] for d in data[::-1]]
    return data


class LendingAMM:
    def __init__(self, A, crypto_amount, upper_price, fee=0.005):
        self.A = A
        self.y0 = float(crypto_amount)
        self.p_up = float(upper_price)  # p_up corresponds to just initial upper price...
        self.p_down = float(upper_price) * (A - 1) / A
        self.p_oracle = self.p_up
        self.y = self.y0
        self.x = 0

        self.price = self.p_up
        self.fee = fee

    def set_oracle(self, p):
        self.p_oracle = p

        if self.x == 0:
            self.y0 = self.y
            return

        if self.y == 0:
            y0 = self.x / self.p_up * sqrt(self.A / (self.A - 1))
            self.y0 = y0
            return

        # Gulp

        D = self.p_up**3 / p**3 * (self.A - 1)**2 * self.x**2 +\
            p**3 / self.p_up * self.A**2 * self.y**2 +\
            2 * self.p_up * self.A*(self.A - 1) * self.x * self.y +\
            4 * self.x * self.y * self.p_up * self.A

        b = self.p_up**1.5 / p**1.5 * (self.A - 1) * self.x +\
            p**1.5 / sqrt(self.p_up) * self.A * self.y

        y0 = (b + sqrt(D)) / (2 * self.p_up * self.A)
        self.y0 = y0

        if self.x > 0 and self.y > 0:
            self.price = self.current_price()

    def gulp(self):
        self.set_oracle(self.p_oracle)

    def f(self):
        return self.y0 * self.p_oracle**1.5 / sqrt(self.p_up) * self.A

    def g(self):
        return self.y0 * self.p_up**1.5 / self.p_oracle**1.5 * (self.A - 1)

    def inv(self):
        return self.p_up * self.A**2 * self.y0**2

    def current_price(self):
        return (self.f() + self.x) / (self.g() + self.y)

    def lower_price(self):
        x = self.f()
        y = self.inv() / x
        return x / y

    def upper_price(self):
        y = self.g()
        x = self.inv() / y
        return x / y

    def trade_to(self, p):
        p_cur = self.price
        p_up = self.upper_price()
        p_down = self.lower_price()

        if p_cur > p_up:
            if p >= p_up:
                self.price = p
                return
            else:
                p_start = p_up
                if p < p_down:
                    p_end = p_down
                else:
                    p_end = p

        elif p_cur < p_down:
            if p <= p_down:
                self.price = p
                return
            else:
                p_start = p_down
                if p > p_up:
                    p_end = p_up
                else:
                    p_end = p

        else:
            p_start = p_cur
            if p > p_up:
                p_end = p_up
            elif p < p_down:
                p_end = p_down
            else:
                p_end = p

        y_start = self.A * self.y0 * sqrt(self.p_up / p_start)
        x_start = self.A * self.y0 * sqrt(self.p_up * p_start)
        # y_end = self.A * self.y0 * sqrt(self.p_up / p_end)
        x_end = self.A * self.y0 * sqrt(self.p_up * p_end)

        value_start = x_start + y_start * p_start
        fee_frac = abs(x_start - x_end) * self.fee / value_start
        self.x *= (1 + fee_frac)
        self.y *= (1 + fee_frac)
        self.y0 *= (1 + fee_frac)
        # if y_start > y_end:
        #     self.y += (y_start - y_end) * self.fee
        # else:
        #     self.x += (x_start - x_end) * self.fee
        # self.gulp()  # -> recalcs y0
        if p_end == p_up:
            self.y = 0
            self.x = max(self.A * self.y0 * sqrt(self.p_up * p_end) - self.f(), 0)
        elif p_end == p_down:
            self.x = 0
            self.y = max(self.A * self.y0 * sqrt(self.p_up / p_end) - self.g(), 0)
        else:
            self.x = max(self.A * self.y0 * sqrt(self.p_up * p_end) - self.f(), 0)
            self.y = max(self.A * self.y0 * sqrt(self.p_up / p_end) - self.g(), 0)
            self.price = p_end

        self.price = p


price_data = load_prices('data/ethusdt-1m.json.gz')


def trader(A, fee, position, size, log=False, verbose=False):
    """
    position: 0..1
    size: 0..1
    """
    data = price_data[int(position * len(price_data) / 2):int((position + size) * len(price_data) / 2)]
    ema = data[0][1]
    ema_t = data[0][0]
    amm = LendingAMM(A, 100, ema, fee=fee)  # A=10, 100 ETH, 400 USD "liquidation" price
    initial_y0 = amm.y0

    losses = []

    for t, o, high, low, c, vol in data:
        ema_mul = 2 ** (- (t - ema_t) / (1000 * T))
        ema = ema * ema_mul + (low + high) / 2 * (1 - ema_mul)
        ema_t = t
        amm.set_oracle(ema)
        high *= (1 - amm.fee - EXT_FEE)
        low *= (1 + amm.fee + EXT_FEE)
        if high > amm.price:
            amm.trade_to(high)
        if low < amm.price:
            amm.trade_to(low)
        d = datetime.fromtimestamp(t//1000).strftime("%Y/%m/%d %H:%M")
        loss = amm.y0 / initial_y0 * 100
        if log:
            print(f'{d}\t{o:.2f}\t{ema:.2f}\t{amm.price:.2f}\t{amm.x:.1f}\t{amm.y:.1f}\t\t{loss:.2f}%')
        if verbose:
            losses.append([t//1000, loss / 100])

    loss = 1 - amm.y0 / initial_y0

    if verbose:
        return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5, losses
    else:
        return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5


def f(x):
    A, fee, pos, size = x
    return trader(A, fee, pos, size, verbose=False, log=False)


pool = Pool(cpu_count())


def get_loss_rate(A, fee, samples=SAMPLES):
    dt = 86400 * 1000 / (price_data[-1][0] - price_data[0][0])
    inputs = [(A, fee, random.random(), (MAX_LOAN_DURATION-MIN_LOAN_DURATION) * dt * random.random()**2 + MIN_LOAN_DURATION*dt) for _ in range(samples)]
    result = pool.map(f, inputs)
    # return sum(result) / samples * 86400**0.5  # loss * sqrt(days)
    # return max(result) * 86400**0.5  # loss * sqrt(days)
    return sum(sorted(result)[::-1][:samples//20]) / (samples / 20) * 86400**.5  # top 10 losses
    # return (sum(r**2 for r in result) / samples * 86400)**0.5  # loss * sqrt(days)


if __name__ == '__main__':
    import pylab
    import numpy as np

    A = np.logspace(np.log10(2), np.log10(40), 20)
    fee = 0.001
    losses = []
    for a in A:
        losses.append(get_loss_rate(a, fee))
        print(a, losses[-1])

    pylab.plot(A, losses)
    pylab.show()
