##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################


import numpy as np
from enum import Enum


from ...utils.global_vars import gDaysInYear
from ...utils.FinError import FinError
from ...products.equity.FinEquityOption import FinEquityOption
from ...utils.helpers import labelToString, check_argument_types
from ...utils.date import Date
from ...market.discount.curve import DiscountCurve
from ...models.gbm_process_simulator import getPaths

from numba import njit

from ...utils.math import NVect

###############################################################################
# TODO: Implement Sobol random numbers
# TODO: Improve convergence
###############################################################################


class FinTouchOptionPayoffTypes(Enum):
    DOWN_AND_IN_CASH_AT_HIT = 1,         # S0>H pays $1 at hit time from above
    UP_AND_IN_CASH_AT_HIT = 2,           # S0<H pays $1 at hit time from below
    DOWN_AND_IN_CASH_AT_EXPIRY = 3,      # S0>H pays $1 at T if hit from below
    UP_AND_IN_CASH_AT_EXPIRY = 4,        # S0<H pays $1 at T if hit from below
    DOWN_AND_OUT_CASH_OR_NOTHING = 5,    # S0>H pays $1 at T if S>H for all t<T
    UP_AND_OUT_CASH_OR_NOTHING = 6,      # S0<H pays $1 at T if S<H for all t<T
    DOWN_AND_IN_ASSET_AT_HIT = 7,        # S0>H pays H at hit time from above
    UP_AND_IN_ASSET_AT_HIT = 8,          # S0>H pays H at hit time from below
    DOWN_AND_IN_ASSET_AT_EXPIRY = 9,     # S0>H pays S(T) at T if S<H for t < T
    UP_AND_IN_ASSET_AT_EXPIRY = 10,      # S0<H pays S(T) at T if S>H for t < T
    DOWN_AND_OUT_ASSET_OR_NOTHING = 11,  # S0>H pays S(T) at T if S>H for t < T
    UP_AND_OUT_ASSET_OR_NOTHING = 12     # S0<H pays S(T) at T if S<H for t < T

###############################################################################


@njit(fastmath=True, cache=True)
def _barrierPayOneAtHitPVDown(s, H, r, dt):
    """ Pay $1 if the stock crosses the barrier H from above. PV payment. """
    num_paths, numTimeSteps = s.shape
    pv = 0.0

    for ip in range(0, num_paths):
        hitFlag = 0

        for it in range(0, numTimeSteps):
            if s[ip][it] <= H:
                hitTime = dt * it
                v = np.exp(-r * hitTime)
                hitFlag = 1
                break

        pv = pv + v * hitFlag

    pv = pv / num_paths
    return pv

###############################################################################


@njit(fastmath=True, cache=True)
def _barrierPayOneAtHitPVUp(s, H, r, dt):
    """ Pay $1 if the stock crosses the barrier H from below. PV payment. """

    num_paths, numTimeSteps = s.shape
    pv = 0.0

    for ip in range(0, num_paths):
        hitFlag = 0

        for it in range(0, numTimeSteps):
            if s[ip][it] >= H:
                hitTime = dt * it
                v = np.exp(-r * hitTime)
                hitFlag = 1
                break

        pv = pv + v * hitFlag

    pv = pv / num_paths
    return pv

###############################################################################


@njit(fastmath=True, cache=True)
def _barrierPayAssetAtExpiryDownOut(s, H):
    """ Pay $1 if the stock crosses the barrier H from above. PV payment. """
    num_paths, numTimeSteps = s.shape
    pv = 0.0

    for ip in range(0, num_paths):
        hitFlag = 1

        for it in range(0, numTimeSteps):
            if s[ip][it] <= H:
                hitFlag = 0
                break

        pv = pv + hitFlag * s[ip][numTimeSteps-1]

    pv = pv / num_paths
    return pv

###############################################################################


@njit(fastmath=True, cache=True)
def _barrierPayAssetAtExpiryUpOut(s, H):
    """ Pay $1 if the stock crosses the barrier H from below. PV payment. """

    num_paths, numTimeSteps = s.shape
    pv = 0.0

    for ip in range(0, num_paths):
        hitFlag = 1

        for it in range(0, numTimeSteps):
            if s[ip][it] >= H:
                hitFlag = 0
                break

        pv = pv + hitFlag * s[ip][numTimeSteps-1]

    pv = pv / num_paths
    return pv

###############################################################################


class FinEquityOneTouchOption(FinEquityOption):
    """ A FinEquityOneTouchOption is an option in which the buyer receives one
    unit of cash OR stock if the stock price touches a barrier at any time
    before the option expiry date and zero otherwise. The choice of cash or
    stock is made at trade initiation. The single barrier payoff must define
    whether the option pays or cancels if the barrier is touched and also when
    the payment is made (at hit time or option expiry). All of these variants
    are all members of the FinTouchOptionTypes enumerated type. """

    def __init__(self,
                 expiry_date: Date,
                 optionType: FinTouchOptionPayoffTypes,
                 barrierPrice: float,
                 paymentSize: float = 1.0):
        """ Create the one touch option by defining its expiry date and the
        barrier level and a payment size if it is a cash . """

        check_argument_types(self.__init__, locals())

        self._expiry_date = expiry_date
        self._optionType = optionType
        self._barrierPrice = float(barrierPrice)
        self._paymentSize = paymentSize

###############################################################################

    def value(self,
              valuation_date: Date,
              stock_price: (float, np.ndarray),
              discount_curve: DiscountCurve,
              dividendCurve: DiscountCurve,
              model):
        """ Equity One-Touch Option valuation using the Black-Scholes model
        assuming a continuous (American) barrier from value date to expiry.
        Handles both cash-or-nothing and asset-or-nothing options."""

        DEBUG_MODE = False

        if valuation_date > self._expiry_date:
            raise FinError("Value date after expiry date.")

        t = (self._expiry_date - valuation_date) / gDaysInYear
        t = max(t, 1e-6)

        s0 = stock_price
        H = self._barrierPrice
        K = self._paymentSize

        sqrtT = np.sqrt(t)

        df = discount_curve.df(self._expiry_date)
        r = discount_curve.ccRate(self._expiry_date)
        q = dividendCurve.ccRate(self._expiry_date)

        v = model._volatility
        v = max(v, 1e-6)

        # Using notation in Haug page 177
        b = r - q
        mu = (b - v * v / 2.0) / v / v
        lam = np.sqrt(mu * mu + 2.0 * r / v / v)

        if DEBUG_MODE:
            print("t:", t)
            print("vol", v)
            print("b", b)
            print("mu", mu)
            print("lam", lam)

        if self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_CASH_AT_HIT:
            # HAUG 1

            if np.any(s0 <= H):
                raise FinError("Stock price is currently below barrier.")

            eta = 1.0
            z = np.log(H/s0) / v / sqrtT + lam * v * sqrtT
            A5_1 = np.power(H/s0, mu + lam) * NVect(eta * z)
            A5_2 = np.power(H/s0, mu - lam) * NVect(eta * z - 2.0 * eta * lam * v * sqrtT)
            v = (A5_1 + A5_2) * K
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_CASH_AT_HIT:
            # HAUG 2

            if np.any(s0 >= H):
                raise FinError("Stock price is currently above barrier.")

            eta = -1.0
            z = np.log(H/s0) / v / sqrtT + lam * v * sqrtT
            A5_1 = np.power(H/s0, mu + lam) * NVect(eta * z)
            A5_2 = np.power(H/s0, mu - lam) * NVect(eta * z - 2.0 * eta * lam * v * sqrtT)
            v = (A5_1 + A5_2) * K
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_ASSET_AT_HIT:
            # HAUG 3

            if np.any(s0 <= H):
                raise FinError("Stock price is currently below barrier.")

            eta = 1.0
            K = H
            z = np.log(H/s0) / v / sqrtT + lam * v * sqrtT
            A5_1 = np.power(H/s0, mu + lam) * NVect(eta * z)
            A5_2 = np.power(H/s0, mu - lam) * NVect(eta * z - 2.0 * eta * lam * v * sqrtT)
            v = (A5_1 + A5_2) * K
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_HIT:
            # HAUG 4

            if np.any(s0 >= H):
                raise FinError("Stock price is currently above barrier.")

            eta = -1.0
            K = H
            z = np.log(H/s0) / v / sqrtT + lam * v * sqrtT
            A5_1 = np.power(H/s0, mu + lam) * NVect(eta * z)
            A5_2 = np.power(H/s0, mu - lam) * NVect(eta * z - 2.0 * eta * lam * v * sqrtT)
            v = (A5_1 + A5_2) * K
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_CASH_AT_EXPIRY:
            # HAUG 5

            if np.any(s0 <= H):
                raise FinError("Stock price is currently below barrier.")

            eta = +1.0
            phi = -1.0
            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            B2 = K * df * NVect(phi*x2 - phi*v*sqrtT)
            B4 = K * df * np.power(H/s0, 2.0 * mu) * NVect(eta*y2-eta*v*sqrtT)
            v = (B2 + B4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_CASH_AT_EXPIRY:
            # HAUG 6

            if np.any(s0 >= H):
                raise FinError("Stock price is currently above barrier.")

            eta = -1.0
            phi = +1.0

            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            B2 = K * df * NVect(phi*x2 - phi*v*sqrtT)
            B4 = K * df * np.power(H/s0, 2.0 * mu) * NVect(eta*y2-eta*v*sqrtT)
            v = (B2 + B4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_ASSET_AT_EXPIRY:
            # HAUG 7

            if np.any(s0 <= H):
                raise FinError("Stock price is currently below barrier.")

            eta = +1.0
            phi = -1.0
            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            dq = np.exp(-q*t)
            A2 = s0 * dq * NVect(phi*x2)
            A4 = s0 * dq * np.power(H/s0, 2.0*(mu+1.0)) * NVect(eta*y2)
            v = (A2 + A4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_EXPIRY:
            # HAUG 8

            if np.any(s0 >= H):
                raise FinError("Stock price is currently above barrier.")

            eta = -1.0
            phi = +1.0
            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            dq = np.exp(-q*t)
            A2 = s0 * dq * NVect(phi*x2)
            A4 = s0 * dq * np.power(H/s0, 2.0*(mu+1.0)) * NVect(eta*y2)
            v = (A2 + A4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_OUT_CASH_OR_NOTHING:
            # HAUG 9

            if np.any(s0 <= H):
                raise FinError("Stock price is currently below barrier.")

            eta = +1.0
            phi = +1.0

            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            B2 = K * df * NVect(phi*x2 - phi*v*sqrtT)
            B4 = K * df * np.power(H/s0, 2.0 * mu) * NVect(eta*y2-eta*v*sqrtT)
            v = (B2 - B4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_OUT_CASH_OR_NOTHING:
            # HAUG 10

            if np.any(s0 >= H):
                raise FinError("Stock price is currently above barrier.")

            eta = -1.0
            phi = -1.0

            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            B2 = K * df * NVect(phi*x2 - phi*v*sqrtT)
            B4 = K * df * np.power(H/s0, 2.0 * mu) * NVect(eta*y2-eta*v*sqrtT)
            v = (B2 - B4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_OUT_ASSET_OR_NOTHING:
            # HAUG 11

            if np.any(s0 <= H):
                raise FinError("Stock price is currently below barrier.")

            eta = +1.0
            phi = +1.0

            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            dq = np.exp(-q*t)
            A2 = s0 * dq * NVect(phi*x2)
            A4 = s0 * dq * np.power(H/s0, 2.0*(mu+1.0)) * NVect(eta*y2)
            v = (A2 - A4)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_OUT_ASSET_OR_NOTHING:
            # HAUG 12

            if np.any(s0 >= H):
                raise FinError("Stock price is currently above barrier.")

            eta = -1.0
            phi = -1.0

            x2 = np.log(s0/H) / v / sqrtT + (mu + 1.0) * v * sqrtT
            y2 = np.log(H/s0) / v / sqrtT + (mu + 1.0) * v * sqrtT
            dq = np.exp(-q*t)
            A2 = s0 * dq * NVect(phi*x2)
            A4 = s0 * dq * np.power(H/s0, 2.0*(mu+1.0)) * NVect(eta*y2)
            v = (A2 - A4)
            return v

        else:
            raise FinError("Unknown option type.")

        return v

###############################################################################

    def valueMC(self,
                valuation_date: Date,
                stock_price: float,
                discount_curve: DiscountCurve,
                dividendCurve: DiscountCurve,
                model,
                num_paths: int = 10000,
                num_steps_per_year: int = 252,
                seed: int = 4242):
        """ Touch Option valuation using the Black-Scholes model and Monte
        Carlo simulation. Accuracy is not great when compared to the analytical
        result as we only observe the barrier a finite number of times. The
        convergence is slow. """

        t = (self._expiry_date - valuation_date) / gDaysInYear

        df = discount_curve.df(self._expiry_date)
        r = -np.log(df)/t

        dq = dividendCurve.df(self._expiry_date)
        q = -np.log(dq)/t

        numTimeSteps = int(t * num_steps_per_year) + 1
        dt = t / numTimeSteps

        v = model._volatility
        s0 = stock_price
        mu = r - q

        s = getPaths(num_paths, numTimeSteps, t, mu, s0, v, seed)

        H = self._barrierPrice
        X = self._paymentSize

        v = 0.0

        if self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_CASH_AT_HIT:
            # HAUG 1

            if s0 <= H:
                raise FinError("Barrier has ALREADY been crossed.")

            v = _barrierPayOneAtHitPVDown(s, H, r, dt)
            v = v * X
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_CASH_AT_HIT:
            # HAUG 2

            if s0 >= H:
                raise FinError("Barrier has ALREADY been crossed.")

            v = _barrierPayOneAtHitPVUp(s, H, r, dt)
            v = v * X
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_ASSET_AT_HIT:
            # HAUG 3

            if s0 <= H:
                raise FinError("Stock price is currently below barrier.")

            v = _barrierPayOneAtHitPVDown(s, H, r, dt) * H
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_HIT:
            # HAUG 4

            if s0 >= H:
                raise FinError("Stock price is currently below barrier.")

            v = _barrierPayOneAtHitPVUp(s, H, r, dt) * H
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_CASH_AT_EXPIRY:
            # HAUG 5

            if s0 <= H:
                raise FinError("Barrier has  ALREADY been crossed.")

            v = _barrierPayOneAtHitPVDown(s, H, 0.0, dt)
            v = v * X * np.exp(-r*t)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_CASH_AT_EXPIRY:
            # HAUG 6

            if s0 >= H:
                raise FinError("Barrier has ALREADY been crossed.")

            v = _barrierPayOneAtHitPVUp(s, H, 0.0, dt)
            v = v * X * np.exp(-r*t)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_IN_ASSET_AT_EXPIRY:
            # HAUG 7

            if s0 <= H:
                raise FinError("Stock price is currently below barrier.")

            v = _barrierPayOneAtHitPVDown(s, H, 0.0, dt) * H
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_EXPIRY:
            # HAUG 8

            if s0 >= H:
                raise FinError("Stock price is currently below barrier.")

            v = _barrierPayOneAtHitPVUp(s, H, 0.0, dt) * H
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_OUT_CASH_OR_NOTHING:
            # HAUG 9

            if s0 <= H:
                raise FinError("Barrier has ALREADY been crossed.")

            v = 1.0 - _barrierPayOneAtHitPVDown(s, H, 0.0, dt)
            v = v * X * np.exp(-r*t)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_OUT_CASH_OR_NOTHING:
            # HAUG 10

            if s0 >= H:
                raise FinError("Barrier has ALREADY been crossed.")

            v = 1.0 - _barrierPayOneAtHitPVUp(s, H, 0.0, dt)
            v = v * X * np.exp(-r*t)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.DOWN_AND_OUT_ASSET_OR_NOTHING:
            # HAUG 11

            if s0 <= H:
                raise FinError("Stock price is currently below barrier.")

            v = _barrierPayAssetAtExpiryDownOut(s, H)
            v = v * np.exp(-r*t)
            return v

        elif self._optionType == FinTouchOptionPayoffTypes.UP_AND_OUT_ASSET_OR_NOTHING:
            # HAUG 12

            if s0 >= H:
                raise FinError("Stock price is currently below barrier.")

            v = _barrierPayAssetAtExpiryUpOut(s, H)
            v = v * np.exp(-r*t)
            return v
        else:
            raise FinError("Unknown option type.")

        return v

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("EXPIRY DATE", self._expiry_date)
        s += labelToString("OPTION TYPE", self._optionType)
        s += labelToString("BARRIER LEVEL", self._barrierPrice)
        s += labelToString("PAYMENT SIZE", self._paymentSize, "")
        return s

###############################################################################

    def _print(self):
        """ Simple print function for backward compatibility. """
        print(self)

###############################################################################
