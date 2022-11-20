from libmodel import LendingAMM

amm = LendingAMM(3000.0, 100.0)
amm.bands_x[0] = 1000.0
amm.bands_y[0] = 1.0

for mul in [1.00, 1.02, 0.98, 1.1, 0.90]:
    p_oracle = amm.p_base * mul
    amm.p_oracle = p_oracle
    y0 = amm.get_y0()
    f = amm.get_f()
    g = amm.get_g()
    x = amm.bands_x[0]
    y = amm.bands_y[0]
    print(f'p_oracle = {p_oracle}')
    print('==========================')
    print(f'y0 = {y0}')
    print(f'f = {f}')
    print(f'g = {g}')
    print('Inv from x, y:')
    print((x + f) * (y + g))
    print('Inv from y0')
    print(amm.p_oracle * amm.A**2 * y0**2)
    print()
