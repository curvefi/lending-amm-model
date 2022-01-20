# import pytest
# from hypothesis import given
# import hypothesis.strategies as st
from libmodel import LendingAMM


def test_p_up_down():
    amm = LendingAMM(p_base=1000, A=100)

    for i in range(-100, 100):
        p_up = amm.p_up(i)
        p_down = amm.p_down(i)
        assert p_up > p_down
        assert amm.p_down(i + 1) == p_up
