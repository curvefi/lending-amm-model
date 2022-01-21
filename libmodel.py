from collections import defaultdict
from math import log, floor


class LendingAMM:
    def __init__(self, p_base, A):
        self.p_base = p_base
        self.p_oracle = p_base
        self.A = A
        self.bands_x = defaultdict(float)
        self.bands_y = defaultdict(float)
        self.active_band = 0

    # Deposit:
    # - above active band - only in y,
    # - below active band - only in x
    # - transform band prices: p_band = p_oracle**3 / p_base**2
    # - add transformation to get_band, get_band_n, deposit_range
    # - add y0 ("invariant") changing with p_oracle
    # - get_price depending on current state (band, x[band], y[band])
    # - trade cross-bands: given dx or dy, calculate the destination band / move
    # - fees:
    #  - collect fees separately for the protocol (wohoo), compensate traded bands
    #  - reduced_input *= (1 - fee), calc output for reduced_input, split fee * input across bands touched

    def p_down(self, n_band):
        """
        Upper price for the band at the current p_oracle
        """
        k = (self.A - 1) / self.A  # equal to (p_up / p_down)
        p_base = self.p_base * k ** n_band
        return self.p_oracle**3 / p_base**2

    def p_up(self, n_band):
        """
        Lower price for the band at the current p_oracle
        """
        k = (self.A - 1) / self.A  # equal to (p_up / p_down)
        p_base = self.p_base * k ** (n_band + 1)
        return self.p_oracle**3 / p_base**2

    def p_top(self, n):
        k = (self.A - 1) / self.A  # equal to (p_up / p_down)
        # Prices which show start and end of band when p_oracle = p
        return self.p_base * k ** n

    def p_bottom(self, n):
        k = (self.A - 1) / self.A  # equal to (p_up / p_down)
        return self.p_top(n) * k

    def get_band_n(self, p):
        """
        Rounds correct way for both higher and lower prices
        """
        k = (self.A - 1) / self.A  # equal to (p_up / p_down)
        return floor(log(p / self.p_base) / log(k))

    def deposit_range(self, amount, p1, p2):
        assert p1 <= self.p_oracle and p2 <= self.p_oracle
        n1 = self.get_band_n(p1)
        n2 = self.get_band_n(p2)
        n1, n2 = sorted([n1, n2])
        y = amount / (n2 - n1 + 1)
        for i in range(n1, n2 + 1):
            assert self.bands_x[i] == 0
            self.bands_y[i] += y

    def get_y0(self):
        A = self.A
        n = self.active_band
        x = self.bands_x[n]
        y = self.bands_y[n]
        p_o = self.p_oracle
        p_top = self.p_top(n)

        return (
            (p_top / p_o)**1.5 * (A - 1) * x + p_o**1.5 / p_top**0.5 * A * y +
            ((p_top/p_o)**3 * (A - 1)**2 * x**2 + p_o**3/p_top * A**2 * y**2 +
             2 * p_top * A*(A-1) * x*y + 4 * x*y * p_top * A) ** 0.5
        ) / (2 * p_top * A)

    def get_f(self, y0=None):
        if y0 is None:
            y0 = self.get_y0()
        p_top = self.p_top(self.active_band)
        p_oracle = self.p_oracle
        return y0 * p_oracle**1.5 / p_top**0.5 * self.A

    def get_g(self, y0=None):
        if y0 is None:
            y0 = self.get_y0()
        p_top = self.p_top(self.active_band)
        p_oracle = self.p_oracle
        return y0 * p_top**1.5 / p_oracle**1.5 * (self.A - 1)

    def get_p(self, y0=None):
        if y0 is None:
            y0 = self.get_y0()
        x = self.bands_x[self.active_band]
        y = self.bands_y[self.active_band]
        return (self.get_f(y0) + x) / (self.get_g(y0) + y)

    def trade_to_price(self, price):
        """
        Not the method to be present in real smart contract, for simulations only
        """
        current_price = self.get_p()
        if price > current_price:
            bstep = 1  # going up: sell
        elif price < current_price:
            bstep = -1  # going down: buy
        else:
            return

        dx = 0
        dy = 0

        while True:
            # XXX handle bands with (0, 0)
            n = self.active_band
            y0 = self.get_y0()
            g = self.get_g(y0)
            f = self.get_f(y0)
            x = self.bands_x[n]
            y = self.bands_y[n]
            # (f + x)(g + y) = const = p_top * A**2 * y0**2 = I
            Inv = (f + x) * (g + y)
            # p = (f + x) / (g + y) => p * (g + y)**2 = I or (f + x)**2 / p = I

            if x == 0 and y == 0:
                if price >= self.p_down(n) and price <= self.p_up(n):
                    break
                self.active_band += bstep

            if bstep == 1:
                # reduce y, increase x, go up
                y_dest = (Inv / price)**0.5 - g
                if y_dest >= 0:
                    # End the cycle
                    self.bands_y[n] = y_dest
                    self.bands_x[n] = Inv / (g + y_dest) - f
                    break

                else:
                    self.bands_y[n] = 0
                    self.bands_x[n] = Inv / g - f
                    self.active_band += 1

            else:
                # increase y, reduce x, go down
                x_dest = (Inv * price)**0.5 - f
                if x_dest >= 0:
                    # End the cycle
                    self.bands_x[n] = x_dest
                    self.bands_y[n] = Inv / (f + x_dest) - g
                    break

                else:
                    self.bands_x[n] = 0
                    self.bandx_y[n] = Inv / f - g
                    self.active_band -= 1

            dx += self.bands_x[n] - x
            dy += self.bands_y[n] - y

        return dx, dy
