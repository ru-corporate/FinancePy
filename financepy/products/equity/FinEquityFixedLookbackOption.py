##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

import numpy as np


from ...utils.math import N
from ...utils.global_vars import gDaysInYear, gSmall
from ...utils.FinError import FinError
from ...utils.date import Date

from ...models.gbm_process_simulator import FinGBMProcess
from ...products.equity.FinEquityOption import FinEquityOption
from ...utils.helpers import labelToString, check_argument_types
from ...market.discount.curve import DiscountCurve
from ...utils.global_types import FinOptionTypes

##########################################################################
# TODO: Attempt control variate adjustment to monte carlo
# TODO: Sobol for Monte Carlo
# TODO: TIGHTEN UP LIMIT FOR W FROM 100
# TODO: Vectorise the analytical pricing formula
##########################################################################


##########################################################################
# FIXED STRIKE LOOKBACK CALL PAYS MAX(SMAX-K,0)
# FIXED STRIKE LOOKBACK PUT PAYS MAX(K-SMIN,0)
##########################################################################


class FinEquityFixedLookbackOption(FinEquityOption):
    """ This is an equity option in which the strike of the option is fixed but
    the value of the stock price used to determine the payoff is the maximum
    in the case of a call option, and a minimum in the case of a put option."""

    def __init__(self,
                 expiry_date: Date,
                 optionType: FinOptionTypes,
                 strikePrice: float):
        """ Create the FixedLookbackOption by specifying the expiry date, the
        option type and the option strike. """

        check_argument_types(self.__init__, locals())

        if optionType != FinOptionTypes.EUROPEAN_CALL and optionType != FinOptionTypes.EUROPEAN_PUT:
            raise FinError("Option type must be EUROPEAN_CALL or EUROPEAN_PUT")

        self._expiry_date = expiry_date
        self._optionType = optionType
        self._strikePrice = strikePrice

###############################################################################

    def value(self,
              valuation_date: Date,
              stock_price: float,
              discount_curve: DiscountCurve,
              dividendCurve: DiscountCurve,
              volatility: float,
              stockMinMax: float):
        """ Valuation of the Fixed Lookback option using Black-Scholes using
        the formulae derived by Conze and Viswanathan (1991). One of the inputs
        is the minimum of maximum of the stock price since the start of the
        option depending on whether the option is a call or a put. """

        t = (self._expiry_date - valuation_date) / gDaysInYear

        df = discount_curve.df(self._expiry_date)
        r = -np.log(df)/t

        dq = dividendCurve.df(self._expiry_date)
        q = -np.log(dq)/t

        v = volatility
        s0 = stock_price
        k = self._strikePrice
        smin = 0.0
        smax = 0.0

        if self._optionType == FinOptionTypes.EUROPEAN_CALL:
            smax = stockMinMax
            if smax < s0:
                raise FinError("The Smax value must be >= the stock price.")
        elif self._optionType == FinOptionTypes.EUROPEAN_PUT:
            smin = stockMinMax
            if smin > s0:
                raise FinError("The Smin value must be <= the stock price.")

        # There is a risk of an overflow in the limit of q=r which
        # we remove by adjusting the value of the dividend
        if abs(r - q) < gSmall:
            q = r + gSmall

        df = np.exp(-r * t)
        dq = np.exp(-q * t)
        b = r - q
        u = v * v / 2.0 / b
        w = 2.0 * b / (v * v)
        expbt = np.exp(b * t)
        sqrtT = np.sqrt(t)

        # Taken from Hull Page 536 (6th edition) and Haug Page 143
        if self._optionType == FinOptionTypes.EUROPEAN_CALL:

            if k > smax:

                d1 = (np.log(s0 / k) + (b + v * v/2.0) * t) / v / sqrtT
                d2 = d1 - v * sqrtT

                if s0 == k:
                    term = -N(d1-2.0 * b * sqrtT / v) + expbt * N(d1)
                elif s0 < k and w > 100.0:
                    term = expbt * N(d1)
                else:
                    term = -np.power(s0 / k, -w) * N(d1 - 2 * b * sqrtT / v) \
                        + expbt * N(d1)

                v = s0 * dq * N(d1) - k * df * N(d2) + s0 * df * u * term

            else:
                e1 = (np.log(s0/smax) + (r - q + v*v/2) * t) / v / sqrtT
                e2 = e1 - v * sqrtT

                if s0 == smax:
                    term = -N(e1 - 2.0 * b * sqrtT / v) + expbt * N(e1)
                elif s0 < smax and w > 100.0:
                    term = expbt * N(e1)
                else:
                    term = (-(s0 / smax)**(-w)) * \
                        N(e1 - 2.0 * b * sqrtT / v) + expbt * N(e1)

                v = df * (smax - k) + s0 * dq * N(e1) - \
                    smax * df * N(e2) + s0 * df * u * term

        elif self._optionType == FinOptionTypes.EUROPEAN_PUT:

            if k >= smin:
                f1 = (np.log(s0/smin) + (b + v * v / 2.0) * t) / v / sqrtT
                f2 = f1 - v * sqrtT

                if s0 == smin:
                    term = N(-f1 + 2.0 * b * sqrtT / v) - expbt * N(-f1)
                elif s0 > smin and w < -100.0:
                    term = -expbt * N(-f1)
                else:
                    term = ((s0 / smin)**(-w)) * N(-f1 + 2.0 * b * sqrtT / v) \
                        - expbt * N(-f1)

                v = df * (k - smin) - s0 * dq * N(-f1) + \
                    smin * df * N(-f2) + s0 * df * u * term

            else:
                d1 = (np.log(s0 / k) + (b + v * v / 2) * t) / v / sqrtT
                d2 = d1 - v * sqrtT

                if s0 == k:
                    term = N(-d1 + 2.0 * b * sqrtT / v) - expbt * N(-d1)
                elif s0 > k and w < -100.0:
                    term = -expbt * N(-d1)
                else:
                    term = ((s0 / k)**(-w)) * N(-d1 + 2.0 * b * sqrtT / v) \
                        - expbt * N(-d1)

                v = k * df * N(-d2) - s0 * dq * N(-d1) + s0 * df * u * term

        else:
            raise FinError("Unknown lookback option type:" +
                           str(self._optionType))

        return v

###############################################################################

    def valueMC(self,
                valuation_date: Date,
                stock_price: float,
                discount_curve: DiscountCurve,
                dividendCurve: DiscountCurve,
                volatility: float,
                stockMinMax: float,
                num_paths: int = 10000,
                num_steps_per_year: int = 252,
                seed: int = 4242):
        """ Monte Carlo valuation of a fixed strike lookback option using a
        Black-Scholes model that assumes the stock follows a GBM process. """

        t = (self._expiry_date - valuation_date) / gDaysInYear

        df = discount_curve.df(self._expiry_date)
        r = discount_curve.ccRate(self._expiry_date)
        q = dividendCurve.ccRate(self._expiry_date)

        mu = r - q
        numTimeSteps = int(t * num_steps_per_year)

        optionType = self._optionType
        k = self._strikePrice

        smin = 0.0
        smax = 0.0

        if self._optionType == FinOptionTypes.EUROPEAN_CALL:
            smax = stockMinMax
            if smax < stock_price:
                raise FinError(
                    "Smax must be greater than or equal to the stock price.")
        elif self._optionType == FinOptionTypes.EUROPEAN_PUT:
            smin = stockMinMax
            if smin > stock_price:
                raise FinError(
                    "Smin must be less than or equal to the stock price.")

        model = FinGBMProcess()
        Sall = model.getPaths(num_paths, numTimeSteps, t, mu, stock_price,
                              volatility, seed)

        # Due to antithetics we have doubled the number of paths
        num_paths = 2 * num_paths
        payoff = np.zeros(num_paths)

        if optionType == FinOptionTypes.EUROPEAN_CALL:
            SMax = np.max(Sall, axis=1)
            smaxs = np.ones(num_paths) * smax
            payoff = np.maximum(SMax - k, 0.0)
            payoff = np.maximum(payoff, smaxs - k)
        elif optionType == FinOptionTypes.EUROPEAN_PUT:
            SMin = np.min(Sall, axis=1)
            smins = np.ones(num_paths) * smin
            payoff = np.maximum(k - SMin, 0.0)
            payoff = np.maximum(payoff, k - smins)
        else:
            raise FinError("Unknown lookback option type:" + str(optionType))

        v = payoff.mean() * df
        return v

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("EXPIRY DATE", self._expiry_date)
        s += labelToString("STRIKE PRICE", self._strikePrice)
        s += labelToString("OPTION TYPE", self._optionType, "")
        return s

###############################################################################

    def _print(self):
        """ Simple print function for backward compatibility. """
        print(self)

###############################################################################
