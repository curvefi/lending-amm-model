#!/usr/bin/env python3

import json
import gzip
from datetime import datetime
from libmodel import LendingAMM

MIN_LOAN_DURATION = 1  # day
MAX_LOAN_DURATION = 30  # days
EXT_FEE = 0.0005
SAMPLES = 400
T = 600  # s
A = 100


def load_prices(f, add_reverse=True):
    with gzip.open(f, "r") as f:
        data = json.load(f)
    # timestamp, OHLC, vol
    data = [[int(d[0])] + [float(x) for x in d[1:6]] for d in data]
    if add_reverse:
        t0 = data[-1][0]
        data += [[t0 + (t0 - d[0])] + d[1:] for d in data[::-1]]
    return data


price_data = load_prices('data/ethusdt-1m.json.gz')


def trader(range_size, fee, Texp, position, size, log=False, verbose=False, loss_style='y'):
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
    p0 = data[0][1]
    initial_y0 = 1.0
    p_base = p0 * (A / (A - 1) + 1e-4)
    amm = LendingAMM(p_base, A)

    # Fill ticks with liquidity
    amm.deposit_range(initial_y0, p0 * (1 - range_size), p0)  # 1 ETH

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
        loss = amm.get_all_y() / initial_y0 * 100
        if log:
            print(f'{d}\t{o:.2f}\t{ema:.2f}\t{amm.get_p():.2f}\t\t{loss:.2f}%')
        if verbose:
            losses.append([t//1000, loss / 100])

    # loss = 1 - amm.y0 / initial_y0
    if loss_style == 'y':
        loss = 1 - amm.get_all_y() / initial_y0

        if verbose:
            return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5, losses
        else:
            return loss / ((data[-1][0] - data[0][0]) / 1000)**0.5


if __name__ == '__main__':
    trader(0.5, 5e-4, 6000, 0, 0.5, log=True)
