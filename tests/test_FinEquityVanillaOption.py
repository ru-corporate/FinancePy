###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np

from financepy.utils.global_types import FinOptionTypes
from financepy.products.equity.FinEquityVanillaOption import FinEquityVanillaOption
from financepy.market.discount.curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import FinModelBlackScholes
from financepy.utils.date import Date
from financepy.utils.FinError import FinError


expiryDate = Date(1, 7, 2015)
call_option = FinEquityVanillaOption(expiryDate, 100.0, FinOptionTypes.EUROPEAN_CALL)
put_option = FinEquityVanillaOption(expiryDate, 100.0, FinOptionTypes.EUROPEAN_PUT)

valueDate = Date(1, 1, 2015)
stockPrice = 100
volatility = 0.30
interestRate = 0.05
dividendYield = 0.01
model = FinModelBlackScholes(volatility)
discountCurve = DiscountCurveFlat(valueDate, interestRate)
dividendCurve = DiscountCurveFlat(valueDate, dividendYield)

def test_call_option():
    v = call_option.value(valueDate, stockPrice, discountCurve, dividendCurve, model)
    assert v.round(4) == 9.3021

def test_greeks():
    delta = call_option.delta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    vega = call_option.vega(valueDate, stockPrice, discountCurve, dividendCurve, model)
    theta = call_option.theta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    rho = call_option.rho(valueDate, stockPrice, discountCurve, dividendCurve, model)
    assert [round(x, 4) for x in (delta, vega, theta, rho)] == \
        [0.5762, 27.4034, -10.1289, 23.9608]

def test_put_option():
    v = put_option.value(valueDate, stockPrice, discountCurve, dividendCurve, model)
    assert v.round(4) == 7.3478
    