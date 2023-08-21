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


price_data = load_prices('data/ethusdt-1m.short.json.gz', add_reverse=False)


def trader(spike_index, spike_mul, data, range_size, fee, Texp, log=False, verbose=False, loss_style='y', **kw):
    """
    position: 0..1
    size: 0..1
    """
    emas = []
    ema = data[0][1]
    ema_t = data[0][0]
    for i, (t, _, high, low, _, _) in enumerate(data[1:]):
        ema_mul = 2 ** (- (t - ema_t) / (1000 * Texp))
        extra_mul = 1.0
        if i == spike_index:
            extra_mul = spike_mul
        ema = ema * ema_mul + (low + high) / 2 * (1 - ema_mul) * extra_mul
        ema_t = t
        emas.append(ema)

    p0 = data[0][1]
    initial_y0 = 1.0
    p_base = p0 * (A / (A - 1) + 1e-4)
    initial_x_value = initial_y0 * p_base
    amm = LendingAMM(p_base, A, fee, **kw)

    # Fill ticks with liquidity
    amm.deposit_range(initial_y0, p0 * (1 - range_size), p0)  # 1 ETH
    initial_all_x = amm.get_all_x()

    losses = []
    fees = []

    def find_target_price(p, is_up=True, new=False):
        if is_up:
            for n in range(amm.max_band, amm.min_band - 1, -1):
                p_down = amm.p_down(n)
                dfee = amm.dynamic_fee(n, new=new)
                p_down_ = p_down * (1 + dfee)
                # XXX print(n, amm.min_band, amm.max_band, p_down, p, amm.get_p())
                if p > p_down_:
                    p_up = amm.p_up(n)
                    p_up_ = p_up * (1 + dfee)
                    # if p >= p_up_:
                    #     return p_up
                    # else:
                    return (p - p_down_) / (p_up_ - p_down_) * (p_up - p_down) + p_down
        else:
            for n in range(amm.min_band, amm.max_band + 1):
                p_up = amm.p_up(n)
                dfee = amm.dynamic_fee(n, new=new)
                p_up_ = p_up * (1 - dfee)
                if p < p_up_:
                    p_down = amm.p_down(n)
                    p_down_ = p_down * (1 - dfee)
                    # if p <= p_down_:
                    #     return p_down
                    # else:
                    return p_up - (p_up_ - p) / (p_up_ - p_down_) * (p_up - p_down)

        if is_up:
            return p * (1 - amm.dynamic_fee(amm.min_band, new=False))
        else:
            return p * (1 + amm.dynamic_fee(amm.max_band, new=False))

    for (t, o, high, low, c, vol), ema in zip(data, emas):
        amm.set_p_oracle(ema)
        max_price = amm.p_up(amm.max_band)
        min_price = amm.p_down(amm.min_band)
        high = find_target_price(high * (1 - EXT_FEE), is_up=True, new=True)
        low = find_target_price(low * (1 + EXT_FEE), is_up=False, new=False)
        # high = high * (1 - EXT_FEE - fee)
        # low = low * (1 + EXT_FEE + fee)
        # if high > amm.get_p():
        #     print(high, '/', high_, '/', max_price, '; ', low, '/', low_, '/', min_price)
        if high > amm.get_p():
            amm.trade_to_price(high)
        if high > max_price:
            # Check that AMM has only stablecoins
            for n in range(amm.min_band, amm.max_band + 1):
                assert amm.bands_y[n] == 0
                assert amm.bands_x[n] > 0
        if low < amm.get_p():
            amm.trade_to_price(low)
        if low < min_price:
            # Check that AMM has only collateral
            for n in range(amm.min_band, amm.max_band + 1):
                assert amm.bands_x[n] == 0
                assert amm.bands_y[n] > 0
        d = datetime.fromtimestamp(t//1000).strftime("%Y/%m/%d %H:%M")
        fees.append(amm.dynamic_fee(amm.active_band, new=False))
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

    # fee_addition = min(fees[-len(fees)//10:]) / 2  # IL is 2 times less than the mispricing

    # If we are fully converted regardless - doesn't matter if we have a mispricing from fees or no
    # if c > max_price:
    #     if all(amm.bands_y[n] == 0 for n in range(amm.min_band, amm.max_band + 1)):
    #         fee_addition = 0
    # elif c < min_price:
    #     if all(amm.bands_x[n] == 0 for n in range(amm.min_band, amm.max_band + 1)):
    #         fee_addition = 0

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
        return loss  # + fee_addition

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


if __name__ == '__main__':
    import pylab
    import numpy as np

    data = price_data[-2000:]

    for i, d in enumerate(data[:1000]):
        for j in range(1, 5):
            d[j] *= 1 + 0.25 * (1000 - i) / 1000

    spike_index = 1500
    spikes = np.linspace(0, 1.0, 50)
    losses = []

    for spike in spikes:
        spike_mul = 1 + spike
        loss = trader(spike_index, spike_mul, data, 0.5, 0.006, Texp=866, loss_style='x',
                      dynamic_fee_multiplier=0, use_po_fee=1, po_fee_delay=2)
        print(spike, loss)
        losses.append(loss)

    losses = np.array(losses) - losses[0]

    pylab.plot(spikes, losses)
    pylab.xlabel('Relative oracle spike size')
    pylab.ylabel('Loss increase')
    pylab.show()
