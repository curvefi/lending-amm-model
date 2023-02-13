#!/usr/bin/env python3

import json
import gzip
import random
import math
import numpy as np
from multiprocessing import Pool, cpu_count
from datetime import datetime
from libmodel import LendingAMM

MIN_LOAN_DURATION = 1  # day
MAX_LOAN_DURATION = 30  # days
EXT_FEE = 0.0005
SAMPLES = 400
T = 600  # s
A = 50


def load_prices(f, add_reverse=True):
    with gzip.open(f, "r") as f:
        data = json.load(f)
    # timestamp, OHLC, vol
    data = [[int(d[0])] + [float(x) for x in d[1:6]] for d in data]
    if add_reverse:
        t0 = data[-1][0]
        data += [[t0 + (t0 - d[0])] + d[1:] for d in data[::-1]]
    return data


price_data = load_prices('data/ethusdt-1m.short.json.gz')


def trader(range_size, fee, Texp, position, size, log=False, verbose=False, loss_style='y', p_shift=None):
    """
    position: 0..1
    size: 0..1
    """
    i0 = int(position * len(price_data) / 2)
    i1 = max(i0 - 24*2*60, 0)
    data = price_data[i1:int((position + size) * len(price_data) / 2)]
    emas = []
    ema = data[0][1]
    ema_t = data[0][0]
    for t, _, high, low, _, _ in data:
        ema_mul = 2 ** (- (t - ema_t) / (1000 * Texp))
        ema = ema * ema_mul + (low + high) / 2 * (1 - ema_mul)
        ema_t = t
        emas.append(ema)
    emas = emas[i0 - i1:]

    data = price_data[int(position * len(price_data) / 2):int((position + size) * len(price_data) / 2)]
    if p_shift is None:
        p0 = data[0][1]
    else:
        p0 = data[0][1] * (1 - p_shift)
    initial_y0 = 1.0
    p_base = p0 * (A / (A - 1) + 1e-4)
    initial_x_value = initial_y0 * p_base
    amm = LendingAMM(p_base, A, fee)

    # Fill ticks with liquidity
    amm.deposit_range(initial_y0, p0 * (1 - range_size), p0)  # 1 ETH
    initial_all_x = amm.get_all_x()

    losses = []

    for (t, o, high, low, c, vol), ema in zip(data, emas):
        amm.p_oracle = ema
        high *= (1 - fee - EXT_FEE)
        low *= (1 + fee + EXT_FEE)
        if high > amm.get_p():
            amm.trade_to_price(high)
        if low < amm.get_p():
            amm.trade_to_price(low)
        d = datetime.fromtimestamp(t//1000).strftime("%Y/%m/%d %H:%M")
        if log or verbose:
            if loss_style == 'y':
                loss = amm.get_all_y() / initial_y0 * 100
            elif loss_style == 'x':
                loss = amm.get_all_x() / initial_x_value * 100
            elif loss_style == 'xloss':
                loss = amm.get_all_x() / initial_all_x * 100
            if log:
                print(f'{d}\t{o:.2f}\t{ema:.2f}\t{amm.get_p():.2f}\t\t{loss:.2f}%')
            if verbose:
                losses.append([t//1000, loss / 100])

    # loss = 1 - amm.y0 / initial_y0
    if loss_style.startswith('y'):
        loss = 1 - amm.get_all_y() / initial_y0

        if not loss_style.endswith('raw'):
            if verbose:
                return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5, losses
            else:
                return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5

    elif loss_style == 'x':
        loss = 1 - amm.get_all_x() / initial_all_x
        # loss = 1 - amm.get_all_x() / initial_x_value
        return loss

    if loss_style == 'realdiff':
        invvalue = amm.get_all_x()
        x = sum(amm.bands_x[i] for i in range(-500, 500))
        y = sum(amm.bands_y[i] for i in range(-500, 500))
        p = (high + low) / 2
        return (invvalue - (y * p + x)) / initial_x_value

    if loss_style == 'xloss':
        loss = 1 - amm.get_all_x() / initial_all_x

        if verbose:
            return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5, losses
        else:
            return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5


def f(x):
    range_size, fee, Texp, pos, size, loss_style, p_shift = x
    return trader(range_size, fee, Texp, pos, size, verbose=False, log=False, loss_style=loss_style,
                  p_shift=p_shift)


pool = Pool(cpu_count())


def get_loss_rate(range_size, fee, Texp=T, measure='topmax', samples=SAMPLES,
                  max_loan_duration=MAX_LOAN_DURATION,
                  min_loan_duration=MIN_LOAN_DURATION,
                  n_top_samples=None):
    dt = 86400 * 1000 / (price_data[-1][0] - price_data[0][0])
    ls = 'xloss' if measure == 'xtopmax' else 'y'
    if measure in ('xavg', 'xtopmax2'):
        ls = 'x'
    if 'realdiff' in measure:
        ls = 'realdiff'
        measure = 'xtopmax2'
    inputs = [(range_size, fee, Texp, random.random(), (max_loan_duration-min_loan_duration) * dt * random.random()**2 +
               min_loan_duration*dt, ls, 0) for _ in range(samples)]
    result = pool.map(f, inputs)
    if not n_top_samples:
        n_top_samples = samples // 20
    if measure == "avg":
        return sum(result) / samples * 86400**0.5  # loss * sqrt(days)
    if measure == "max":
        return max(result) * 86400**0.5  # loss * sqrt(days)
    if measure == "topmax":
        return sum(sorted(result)[::-1][:n_top_samples]) / n_top_samples * 86400**.5  # top 5% losses
    if measure == "sqavg":
        return (sum(r**2 for r in result) / samples * 86400)**0.5  # loss * sqrt(days)
    if measure == "xavg":
        return sum(result) / samples
    if measure == "xtopmax":
        return sum(sorted(result)[::-1][:n_top_samples]) / n_top_samples * 86400**0.5
    if measure == "xtopmax2":
        return sum(sorted(result)[::-1][:n_top_samples]) / n_top_samples
    raise Exception("Incorrect measure")


def get_loss_shift(range_size, fee, Texp=T, ls='x', samples=SAMPLES,
                   max_loan_duration=MAX_LOAN_DURATION,
                   min_loan_duration=MIN_LOAN_DURATION,
                   max_p_shift=0.05):
    dt = 86400 * 1000 / (price_data[-1][0] - price_data[0][0])
    inputs = [(range_size, fee, Texp, random.random(), (max_loan_duration-min_loan_duration) * dt * random.random()**2 +
               min_loan_duration*dt, ls, random.random() * max_p_shift) for _ in range(samples)]
    price_shifts = []
    for row in inputs:
        position = row[3]
        size = row[4]
        p_shift = row[6]
        data = price_data[int(position * len(price_data) / 2):int((position + size) * len(price_data) / 2)]
        p0 = data[0][1] * (1 - p_shift)
        min_p = min(d[1] for d in data)
        # print(min_p, p0, position, size)
        price_shifts.append(min_p / p0 - 1)
    result = pool.map(f, inputs)
    return result, price_shifts


def get_loss_variance(range_size, fee, Texp=T, ls='x', samples=SAMPLES,
                   max_loan_duration=MAX_LOAN_DURATION,
                   min_loan_duration=MIN_LOAN_DURATION):
    dt = 86400 * 1000 / (price_data[-1][0] - price_data[0][0])
    inputs = [(range_size, fee, Texp, random.random(), (max_loan_duration-min_loan_duration) * dt * random.random()**2 +
               min_loan_duration*dt, ls, 0) for _ in range(samples)]
    price_variances = []
    for row in inputs:
        position = row[3]
        size = row[4]
        data = price_data[int(position * len(price_data) / 2):int((position + size) * len(price_data) / 2)]
        prices = np.array(list(map(lambda d: (d[2] + d[3]) / 2, data)))
        variance = prices.var()  # abs
        mean = prices.mean()  # abs
        price_variances.append(math.sqrt(variance) / mean)  # sqrt(D) / M [%]
    result = pool.map(f, inputs)
    return result, price_variances


if __name__ == '__main__':
    # get_loss_shift(0.2, 1e-2, Texp=10000, min_loan_duration=3, max_loan_duration=3, samples=400)
    print(get_loss_rate(0.2, 1e-2, measure='realdiff', min_loan_duration=7, max_loan_duration=7, Texp=7000, samples=10000))
    # print(get_loss_rate(0.2, 3e-3, measure='avg', min_loan_duration=30, max_loan_duration=30, Texp=10000))
    # print(get_loss_rate(0.2, 5e-4, measure='avg', min_loan_duration=30, max_loan_duration=30, Texp=10000))
    # print(get_loss_rate(0.2, 0.0, measure='avg', min_loan_duration=30, max_loan_duration=30, Texp=10000))
    # trader(0.50, 30e-4, 600, 0.7, 0.2, log=True, loss_style='xloss')
    # trader(0.50, 30e-4, 600, 0.7, 0.2, log=True, loss_style='y')
    # trader(0.50, 30e-4, 600, 0.7, 0.2, log=True, loss_style='x')
