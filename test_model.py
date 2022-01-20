# import pytest
from hypothesis import given
import hypothesis.strategies as st
from libmodel import LendingAMM

ERROR = 1 + 1e-8


def approx(x, y):
    return 2 * abs(x - y) / abs(x + y)


def test_p_up_down():
    amm = LendingAMM(p_base=1000, A=100)

    for i in range(-100, 100):
        p_up = amm.p_up(i)
        p_down = amm.p_down(i)
        assert p_up > p_down
        assert amm.p_down(i + 1) == p_up


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
