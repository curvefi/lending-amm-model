from libmodel import LendingAMM

amm = LendingAMM(3000, 100)
amm.bands_x[1] = 10
amm.bands_y[1] = 0.9
amm.active_band = 1

for _ in range(20):
    amm.p_oracle *= 0.999
    print('p_oracle: ', amm.p_oracle)
    print('p up/down:', amm.p_up(1), amm.p_down(1))
    print('y0:       ', amm.get_y0())
    print('y_up:     ', amm.get_y_up(1))
    print()

amm.p_oracle = 2940.448501875000000000
amm.bands_x[1] = 1485.0375
amm.bands_y[1] = 0.5074629343981888
print(amm.get_y_up(1))
print(amm.p_up(1), amm.p_down(1))
