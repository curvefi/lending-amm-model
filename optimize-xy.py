#!/usr/bin/env python3
import numpy as np
from scipy.optimize import newton

# Starts from x = 1, y=0, price = p_down = p_up * (A - 1) / A
# Ends at p_up, x=0, y=...
# Need to find y(A) * p_up


x_initial = 1  # Had 1 dollar first
dx = -1e-4  # Step size. The smaller - the more precise it will be
A = 10


def trade_optimize(A):
    x = x_initial
    y = 0  # And 0 collateral
    p_up = 1  # price = 1.0 for simplicity

    xtol = 1e-10

    p_down = p_up * (A - 1) / A

    xx = []
    yy = []

    def F(p):
        # F(p) = (f + x) * (g + y) - p_up * A**2 * y0**2 = 0
        # where y0 is substituted from get_y0(p)

        # 1. Calculate y0 from (f + x) / (g + y) = p
        f = p**2 / p_up * A
        g = p_up / p * (A - 1)
        _up = (p * y - x)
        _down = (f - p * g)
        # y0 = (p * y - x) / (f - p * g)

        # 2. Calculate F
        return (f*_up + x*_down) * (g*_up + y*_down) - p * A**2 * _up**2

    p = p_down
    assert abs(F(p)) < xtol

    while x > xtol:
        f = p**2 / p_up * A
        g = p_up / p * (A - 1)
        y0 = (p * y - x) / (f - p * g)
        f *= y0
        g *= y0

        x += dx
        y = p * A**2 * y0**2 / (f + x) - g

        p = newton(F, p)

        y_up = y + x / (p_up * p)**0.5
        x_down = x + y * (p_down * p)**0.5

        xx.append(x_down)
        yy.append(y_up)

        print("x = {:.4f},  y = {:.4f};   y↑ = {:0.6f},  x↓ = {:.6f}".format(
            x, y, y_up, x_down))

    return y, xx, yy


if __name__ == '__main__':
    y_up, xx, yy = trade_optimize(A)
    x_err = np.abs((np.array(xx) - x_initial)).max() / x_initial
    y_err = np.abs((np.array(yy) - y_up)).max() / y_up

    print()
    print('Amount of collateral after trading:', y_up)
    print('Max relative deviation of x:', x_err)
    print('Max relative deviation of y:', y_err)
    print('Step size:', abs(dx))
    # y = p_up * x0 * sqrt(1 + 1 / (A - 1))
    # and from any point
    # y0 = y + x / sqrt(p_up * p)
    # but only if p = p_oracle
    # So we "trade" to p = p_oracle and then measure
