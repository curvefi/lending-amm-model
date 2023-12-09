from collections import defaultdict
from math import log, floor, sqrt


class LendingAMM:
    def __init__(self, p_base, A, fee=0, dynamic_fee_multiplier=0.0, use_po_fee=1, po_fee_delay=1):
        self.p_base = p_base
        self.p_oracle = p_base
        self.prev_p_oracle = p_base
        self.old_dfee = 0
        self.A = A
        self.bands_x = defaultdict(float)
        self.bands_y = defaultdict(float)
        self.active_band = 0
        self.fee = fee
        self.dynamic_fee_multiplier = dynamic_fee_multiplier
        self.use_po_fee = use_po_fee
        self.po_fee_delay = po_fee_delay
        self.oracle_history = []
        self.deposited = False

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

    def set_p_oracle(self, p):
        if self.use_po_fee:
            if len(self.oracle_history) >= 1:
                self.prev_p_oracle = self.oracle_history[-1]
            else:
                self.prev_p_oracle = self.p_oracle
            self.oracle_history.append(p)
        else:
            self.prev_p_oracle = p
        self.p_oracle = p

    def dynamic_fee(self, n_band, new=True):
        p_up = self.p_up(n_band)
        p_down = self.p_down(n_band)
        diff1 = p_up - self.p_oracle
        diff2 = self.p_oracle - p_down

        fee = self.fee

        if self.use_po_fee:
            if new:
                r = min(self.prev_p_oracle, self.p_oracle) / max(self.prev_p_oracle, self.p_oracle)
                fee = (self.old_dfee + (1 - r**3)) * (self.po_fee_delay - 1) / self.po_fee_delay
                self.old_dfee = fee
                fee = max(fee, self.fee)
            else:
                fee = max(self.old_dfee, self.fee)

        if self.dynamic_fee_multiplier > 0:
            if (p_down > self.p_oracle) or (p_up < self.p_oracle):
                # Fee if not current band
                fee = max(fee, min([abs(diff1), abs(diff2)]) / (2 * self.p_oracle) * self.dynamic_fee_multiplier)
            else:
                # Fee if current band
                fee = max(fee, abs(self.get_p() - self.p_oracle) / (2 * self.p_oracle) * self.dynamic_fee_multiplier)

        return fee

    def p_down(self, n_band):
        """
        Lower price for the band at the current p_oracle
        """
        k = (self.A - 1) / self.A  # equal to (p_down / p_up)
        p_base = self.p_base * k ** n_band
        return self.p_oracle**3 / p_base**2

    def p_up(self, n_band):
        """
        Upper price for the band at the current p_oracle
        """
        k = (self.A - 1) / self.A  # equal to (p_down / p_up)
        p_base = self.p_base * k ** (n_band + 1)
        return self.p_oracle**3 / p_base**2

    def p_top(self, n):
        k = (self.A - 1) / self.A  # equal to (p_down / p_up)
        # Prices which show start and end of band when p_oracle = p
        return self.p_base * k ** n

    def p_bottom(self, n):
        k = (self.A - 1) / self.A  # equal to (p_down / p_up)
        return self.p_top(n) * k

    def get_band_n(self, p):
        """
        Rounds correct way for both higher and lower prices
        """
        k = (self.A - 1) / self.A  # equal to (p_down / p_up)
        return floor(log(p / self.p_base) / log(k))

    def deposit_range(self, amount, p1, p2):
        assert p1 <= self.p_oracle and p2 <= self.p_oracle
        assert not self.deposited

        n1 = self.get_band_n(p1)
        n2 = self.get_band_n(p2)
        n1, n2 = sorted([n1, n2])
        y = amount / (n2 - n1 + 1)
        self.min_band = min(n1, n2)
        self.max_band = max(n1, n2)
        for i in range(n1, n2 + 1):
            assert self.bands_x[i] == 0
            self.bands_y[i] += y

        self.deposited = True

    def deposit_top(self, amount, p, band_shift=0, dn=4):
        assert not self.deposited
        n1 = self.get_band_n(self.p_oracle) + band_shift
        while True:
            n1 += 1
            if p < self.p_down(n1):
                break
        n2 = n1 + dn - 1
        y = amount / dn
        self.min_band = n1
        self.max_band = n2
        for i in range(n1, n2 + 1):
            assert self.bands_x[i] == 0
            self.bands_y[i] += y
        self.deposited = True

    def withdraw(self):
        assert self.deposited
        x = 0
        y = 0
        for i in range(self.min_band, self.max_band + 1):
            x += self.bands_x[i]
            y += self.bands_y[i]
            self.bands_x[i] = 0
            self.bands_y[i] = 0
        self.deposited = False
        return x, y

    def get_y0(self, n=None):
        A = self.A
        if n is None:
            n = self.active_band
        x = self.bands_x[n]
        y = self.bands_y[n]
        p_o = self.p_oracle
        p_top = self.p_top(n)

        # solve:
        # p_o * A * y0**2 - y0 * (p_top/p_o * (A-1) * x + p_o**2/p_top * A * y) - xy = 0
        b = p_top / p_o * (A-1) * x + p_o**2 / p_top * A * y
        a = p_o * A
        D = b**2 + 4 * a * x * y
        return (b + sqrt(D)) / (2 * a)

    def get_f(self, y0=None, n=None):
        if y0 is None:
            y0 = self.get_y0()
        if n is None:
            n = self.active_band
        p_top = self.p_top(n)
        p_oracle = self.p_oracle
        return y0 * p_oracle**2 / p_top * self.A

    def get_g(self, y0=None, n=None):
        if y0 is None:
            y0 = self.get_y0()
        if n is None:
            n = self.active_band
        p_top = self.p_top(n)
        p_oracle = self.p_oracle
        return y0 * p_top / p_oracle * (self.A - 1)

    def get_p(self, y0=None):
        x = self.bands_x[self.active_band]
        y = self.bands_y[self.active_band]
        if x == 0 and y == 0:
            return (self.p_up(self.active_band) * self.p_down(self.active_band)) ** 0.5
        if y0 is None:
            y0 = self.get_y0()
        return (self.get_f(y0) + x) / (self.get_g(y0) + y)

    def trade_to_price(self, price):
        """
        Not the method to be present in real smart contract, for simulations only
        """
        if self.bands_x[self.active_band] == 0 and self.bands_y[self.active_band] == 0:
            if price > self.p_up(self.active_band):
                bstep = 1
            elif price < self.p_down(self.active_band):
                bstep = -1
            else:
                return 0, 0

        else:
            current_price = self.get_p()
            if price > current_price:
                bstep = 1  # going up: sell
            elif price < current_price:
                bstep = -1  # going down: buy
            else:
                return 0, 0

        dx = 0
        dy = 0

        while True:
            n = self.active_band
            y0 = self.get_y0()
            g = self.get_g(y0)
            f = self.get_f(y0)
            x = self.bands_x[n]
            y = self.bands_y[n]
            # (f + x)(g + y) = const = p_oracle * A**2 * y0**2 = I
            Inv = (f + x) * (g + y)
            # p = (f + x) / (g + y) => p * (g + y)**2 = I or (f + x)**2 / p = I

            if x == 0 and y == 0:
                if price >= self.p_down(n) and price <= self.p_up(n):
                    break
                self.active_band += bstep
                continue

            fee = self.dynamic_fee(n)

            if bstep == 1:
                # reduce y, increase x, go up
                y_dest = (Inv / price)**0.5 - g
                x_old = self.bands_x[n]
                if y_dest >= 0:
                    # End the cycle
                    self.bands_y[n] = y_dest
                    self.bands_x[n] = Inv / (g + y_dest) - f
                    delta_x = self.bands_x[n] - x_old
                    self.bands_x[n] += fee * delta_x
                    dx += self.bands_x[n] - x
                    dy += self.bands_y[n] - y
                    break

                else:
                    self.bands_y[n] = 0
                    self.bands_x[n] = Inv / g - f
                    delta_x = self.bands_x[n] - x_old
                    self.bands_x[n] += fee * delta_x
                    self.active_band += 1

            else:
                # increase y, reduce x, go down
                x_dest = (Inv * price)**0.5 - f
                y_old = self.bands_y[n]
                if x_dest >= 0:
                    # End the cycle
                    self.bands_x[n] = x_dest
                    self.bands_y[n] = Inv / (f + x_dest) - g
                    delta_y = self.bands_y[n] - y_old
                    self.bands_y[n] += fee * delta_y
                    dx += self.bands_x[n] - x
                    dy += self.bands_y[n] - y
                    break

                else:
                    self.bands_x[n] = 0
                    self.bands_y[n] = Inv / f - g
                    delta_y = self.bands_y[n] - y_old
                    self.bands_y[n] += fee * delta_y
                    self.active_band -= 1

            dx += self.bands_x[n] - x
            dy += self.bands_y[n] - y

            if abs(n) > 1000:
                raise Exception("We should not be here ever")

        return dx, dy

    def get_y_up(self, n):
        """
        Measure the amount of y in the band n if we adiabatically trade near p_oracle on the way up
        """
        x = self.bands_x[n]
        y = self.bands_y[n]
        p_o = self.p_oracle
        p_o_up = self.p_top(n)
        p_o_down = p_o_up * (self.A - 1) / self.A
        p_current_mid = p_o**3 / p_o_down**2 * (self.A - 1) / self.A
        sqrt_band_ratio = sqrt(self.A / (self.A - 1))

        if x == 0 or y == 0:
            if x == 0 and y == 0:
                return 0

            if p_o > p_o_up:
                # all to y at constant p_o, then to target currency adiabatically
                y_equiv = y
                if y == 0:
                    y_equiv = x / p_current_mid
                return y_equiv

            elif p_o < p_o_down:
                x_equiv = x
                if x == 0:
                    x_equiv = y * p_current_mid
                return x_equiv * sqrt_band_ratio / p_o_up

        y0 = self.get_y0(n)
        g = self.get_g(y0, n)
        f = self.get_f(y0, n)
        # (f + x)(g + y) = const = p_top * A**2 * y0**2 = I
        Inv = (f + x) * (g + y)
        # p = (f + x) / (g + y) => p * (g + y)**2 = I or (f + x)**2 / p = I

        # First, "trade" in this band to p_oracle
        x_o = 0
        y_o = 0

        if p_o > p_o_up:  # p_o < p_current_down, all to y
            # x_o = 0
            y_o = max(Inv / f, g) - g
            return y_o

        elif p_o < p_o_down:  # p_o > p_current_up, all to x
            # y_o = 0
            x_o = max(Inv / g, f) - f
            return x_o * sqrt_band_ratio / p_o_up

        else:
            # y_o__ = max(sqrt(Inv / p_o), g) - g
            # x_o__ = max(Inv / (g + y_o__), f) - f

            # y_o = self.A * y0 * (1 - p_o_down / p_o)
            # x_o = self.A * y0 * p_o * (1 - p_o / p_o_up)

            # print('p_o =', p_o, 'p_o_up =', p_o_up, 'p_o_down =', p_o_down)
            # print('x', x_o__, '->', x_o)
            # print('y', y_o__, '->', y_o)
            # print()

            y_o = self.A * y0 * (1 - p_o_down / p_o)
            x_o = max(Inv / (g + y_o), f) - f

            # Now adiabatic conversion from definitely in-band
            return y_o + x_o / sqrt(p_o_up * p_o)

    def get_x_down(self, n):
        """
        Measure the amount of x in the band n if we adiabatically trade near p_oracle on the way up
        """
        x = self.bands_x[n]
        y = self.bands_y[n]
        p_o = self.p_oracle
        p_o_up = self.p_top(n)
        p_o_down = p_o_up * (self.A - 1) / self.A
        p_current_mid = p_o**3 / p_o_down**2 * (self.A - 1) / self.A
        sqrt_band_ratio = sqrt(self.A / (self.A - 1))

        if x == 0 or y == 0:
            if x == 0 and y == 0:
                return 0

            if p_o > p_o_up:
                # all to y at constant p_o, then to target currency adiabatically
                y_equiv = y
                if y == 0:
                    y_equiv = x / p_current_mid
                return y_equiv * p_o_up / sqrt_band_ratio

            elif p_o < p_o_down:
                x_equiv = x
                if x == 0:
                    x_equiv = y * p_current_mid
                return x_equiv

        y0 = self.get_y0(n)
        g = self.get_g(y0, n)
        f = self.get_f(y0, n)
        # (f + x)(g + y) = const = p_top * A**2 * y0**2 = I
        Inv = (f + x) * (g + y)
        # p = (f + x) / (g + y) => p * (g + y)**2 = I or (f + x)**2 / p = I

        # First, "trade" in this band to p_oracle
        x_o = 0
        y_o = 0

        if p_o > p_o_up:  # p_o < p_current_down, all to y
            # x_o = 0
            y_o = max(Inv / f, g) - g
            return y_o * p_o_up / sqrt_band_ratio

        elif p_o < p_o_down:  # p_o > p_current_up, all to x
            # y_o = 0
            x_o = max(Inv / g, f) - f
            return x_o

        else:
            # y_o = max(sqrt(Inv / p_o), g) - g
            # x_o = max(Inv / (g + y_o), f) - f
            y_o = self.A * y0 * (1 - p_o_down / p_o)
            x_o = max(Inv / (g + y_o), f) - f
            # Now adiabatic conversion from definitely in-band
            return x_o + y_o * sqrt(p_o_down * p_o)

    def get_all_y(self):
        return sum(self.get_y_up(i) for i in range(-500, 500))

    def get_all_x(self):
        return sum(self.get_x_down(i) for i in range(-500, 500))
