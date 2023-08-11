# import pytest
from hypothesis import given
from random import random
import hypothesis.strategies as st
from libmodel import LendingAMM

ERROR = 1 + 1e-8
ABS_ERROR = 1e-5


def approx(x, y):
    return 2 * abs(x - y) / abs(x + y)


def test_p_up_down():
    amm = LendingAMM(p_base=1000, A=100)

    for i in range(-100, 100):
        p_up = amm.p_up(i)
        p_down = amm.p_down(i)
        assert p_up > p_down
        assert amm.p_down(i + 1) == p_up


def test_price_continuity():
    amm = LendingAMM(p_base=1000, A=100)

    for i in range(-100, 100):
        amm.bands_x[i] = 10000 * random() + 1.0
        amm.bands_y[i] = 0.0
        amm.bands_x[i+1] = 0.0
        amm.bands_y[i+1] = 10 * random() + 0.001
        amm.active_band = i
        p1 = amm.get_p()
        amm.active_band = i+1
        p2 = amm.get_p()
        assert abs(p1 - p2) < 1e-8
        assert abs(p1 - amm.p_up(i)) < 1e-8
        assert abs(p2 - amm.p_down(i+1)) < 1e-8


def test_p_top_bottom():
    amm = LendingAMM(p_base=1000, A=100)

    for i in range(-100, 100):
        p = amm.p_top(i)
        amm.p_oracle = p
        assert approx(amm.p_down(i), p) < 1e-12
        p = amm.p_bottom(i)
        amm.p_oracle = p
        assert approx(amm.p_up(i), p) < 1e-12


@given(
    n=st.integers(-10, 10),
    x=st.floats(0, 1e6),
    y=st.floats(0, 1e6),
    p_base=st.floats(0.1, 10000),
    A=st.floats(2, 300)
)
def test_y0(n, x, y, p_base, A):
    amm = LendingAMM(p_base, A)
    amm.active_band = n
    amm.p_oracle = amm.p_top(n)

    p_up = amm.p_up(n)
    p_down = amm.p_down(n)

    amm.bands_x[n] = x
    amm.bands_y[n] = y

    y0 = amm.get_y0()

    assert y0 * ERROR >= y
    assert y0 / ERROR <= y + x / p_down
    assert y0 * ERROR >= y + x / p_up


@given(
    n=st.integers(-10, 10),
    x=st.floats(0, 1e6),
    y=st.floats(0, 1e6),
    p_base=st.floats(0.1, 10000),
    p_oracle=st.floats(0.1, 10000),
    A=st.floats(2, 300)
)
def test_current_price(n, x, y, p_base, p_oracle, A):
    amm = LendingAMM(p_base, A)
    amm.active_band = n
    amm.p_oracle = p_oracle

    p_up = amm.p_up(n)
    p_down = amm.p_down(n)

    amm.bands_x[n] = x
    amm.bands_y[n] = y

    if x == 0 and y == 0:
        return

    p = amm.get_p()

    assert p / ERROR <= p_up
    assert p * ERROR >= p_down


@given(
    n=st.integers(-10, 10),
    p_base=st.floats(0.1, 10000),
    p_oracle=st.floats(0.1, 10000),
    A=st.floats(2, 300),
    p_target=st.floats(0.1, 10000),
    from_n=st.integers(-10, 10),
    to_n=st.integers(-10, 10),
    x=st.floats(0, 1e6),
    y=st.floats(0, 1e6),
)
def test_trade(n, p_base, p_oracle, A, p_target, from_n, to_n, x, y):
    amm = LendingAMM(p_base, A)
    amm.active_band = n
    amm.p_oracle = p_oracle

    # Fill with liquidity
    from_n, to_n = sorted([from_n, to_n])
    for i in range(from_n, to_n + 1):
        if i <= n:
            amm.bands_x[i] = x
        if i >= n:
            amm.bands_y[i] = y

    dx, dy = amm.trade_to_price(p_target)

    # Check that price is in the proper band, and the value is close enough
    assert p_target >= amm.p_down(amm.active_band) / ERROR
    assert p_target <= amm.p_up(amm.active_band) * ERROR
    if amm.bands_x[amm.active_band] > 0 or amm.bands_y[amm.active_band] > 0:
        p_new = amm.get_p()
        assert p_new >= amm.p_down(amm.active_band) / ERROR
        assert p_new <= amm.p_up(amm.active_band) * ERROR
        assert approx(p_new, p_target) < 1e-8

    # Check the sign of the trade direction
    if amm.active_band > n:
        assert dx >= -ABS_ERROR
        assert dy <= ABS_ERROR
    elif amm.active_band < n:
        assert dx <= ABS_ERROR
        assert dy >= -ABS_ERROR

    # Check that we are all in proper currency in ecah band touched
    for i in range(from_n, to_n + 1):
        if (i <= n and x > 0) or (i >= n and y > 0):
            _p = amm.p_down(i)
            if i == n:
                _x = x + y * _p
                _y = y + x / _p
            else:
                if i > n:
                    _x = y * _p
                    _y = y
                if i < n:
                    _x = x
                    _y = x / _p
            if i > amm.active_band:
                assert amm.bands_x[i] == 0
                assert amm.bands_y[i] > 0.1 * _y
            if i < amm.active_band:
                assert amm.bands_y[i] == 0
                assert amm.bands_x[i] > 0.1 * _x


def test_y_up():
    for i in range(-100, 100):
        amm = LendingAMM(p_base=1000, A=10)
        p_top = amm.p_top(i)
        p_bottom = amm.p_bottom(i)

        amm.p_oracle = p_top
        amm.bands_y[i] = 10
        amm.bands_x[i] = 0
        assert approx(amm.get_y_up(i), 10) <= 1e-10

        amm.p_oracle = p_bottom
        amm.bands_y[i] = 0
        amm.bands_x[i] = 10
        assert approx(amm.get_y_up(i), 10 / p_top * (10 / 9)**0.5) <= 1e-10

        amm.p_oracle = (p_top + p_bottom) / 2
        amm.bands_y[i] = 10
        amm.bands_x[i] = 10
        assert approx(amm.get_y_up(i), 10 / p_top + 10) < 0.2
