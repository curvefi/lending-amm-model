#!/usr/bin/env python3
from scipy.optimize import newton

# Starts from x = 1, y=0, price = p_down = p_up * (A - 1) / A
# Ends at p_up, x=0, y=...
# Need to find y(A) * p_up


def trade_optimize(A):
    x = 1
    y = 0
    p_up = 1
    dx = -1e-4

    xtol = 1e-10

    p_down = p_up * (A - 1) / A

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

    return y


if __name__ == '__main__':
    print(trade_optimize(10))
    # y = p_up * x0 * sqrt(1 + 1 / (A - 1))
