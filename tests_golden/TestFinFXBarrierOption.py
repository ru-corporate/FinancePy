###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.models.process_simulator import FinProcessTypes
from financepy.models.process_simulator import FinGBMNumericalScheme
from financepy.models.black_scholes import FinModelBlackScholes
from financepy.products.fx.FinFXBarrierOption import FinFXBarrierTypes
from financepy.products.fx.FinFXBarrierOption import FinFXBarrierOption
from financepy.market.discount.curve_flat import DiscountCurveFlat
from financepy.utils.date import Date

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinFXBarrierOption():

    valuation_date = Date(1, 1, 2015)
    expiry_date = Date(1, 1, 2016)
    spotFXRate = 100.0
    currencyPair = "USDJPY"
    volatility = 0.20
    domInterestRate = 0.05
    forInterestRate = 0.02
    optionType = FinFXBarrierTypes.DOWN_AND_OUT_CALL
    notional = 100.0
    notionalCurrency = "USD"

    drift = domInterestRate - forInterestRate
    scheme = FinGBMNumericalScheme.ANTITHETIC
    processType = FinProcessTypes.GBM
    domDiscountCurve = DiscountCurveFlat(valuation_date, domInterestRate)
    forDiscountCurve = DiscountCurveFlat(valuation_date, forInterestRate)
    model = FinModelBlackScholes(volatility)

    ###########################################################################

    import time
    start = time.time()
    numObservationsPerYear = 100

    for optionType in FinFXBarrierTypes:

        testCases.header("Type", "K", "B", "S", "Value",
                         "ValueMC", "TIME", "Diff")

        for spotFXRate in range(60, 140, 10):
            B = 110.0
            K = 100.0

            option = FinFXBarrierOption(expiry_date, K, currencyPair,
                                        optionType, B,
                                        numObservationsPerYear,
                                        notional, notionalCurrency)

            value = option.value(valuation_date, spotFXRate,
                                 domDiscountCurve, forDiscountCurve, model)

            start = time.time()
            modelParams = (spotFXRate, drift, volatility, scheme)
            valueMC = option.valueMC(valuation_date, spotFXRate,
                                     domInterestRate, processType,
                                     modelParams)

            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value

            testCases.print(optionType, K, B, spotFXRate, value, valueMC,
                            timeElapsed, diff)

        for spotFXRate in range(60, 140, 10):
            B = 100.0
            K = 110.0

            option = FinFXBarrierOption(expiry_date, K, currencyPair,
                                        optionType, B,
                                        numObservationsPerYear,
                                        notional, notionalCurrency)

            value = option.value(valuation_date, spotFXRate,
                                 domDiscountCurve, forDiscountCurve, model)

            start = time.time()
            modelParams = (spotFXRate, drift, volatility, scheme)
            valueMC = option.valueMC(valuation_date,
                                     spotFXRate,
                                     domInterestRate,
                                     processType,
                                     modelParams)

            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value

            testCases.print(optionType, K, B, spotFXRate, value, valueMC,
                            timeElapsed, diff)

    end = time.time()

##########################################################################

    spotFXRates = range(50, 150, 50)
    B = 105.0

    testCases.header("Type", "K", "B", "S:", "Value", "Delta", "Vega", "Theta")

    for optionType in FinFXBarrierTypes:
        for spotFXRate in spotFXRates:
            barrierOption = FinFXBarrierOption(expiry_date,
                                               100.0,
                                               currencyPair,
                                               optionType,
                                               B,
                                               numObservationsPerYear,
                                               notional,
                                               notionalCurrency)

            value = barrierOption.value(valuation_date,
                                        spotFXRate,
                                        domDiscountCurve,
                                        forDiscountCurve,
                                        model)

            delta = barrierOption.delta(valuation_date,
                                        spotFXRate,
                                        domDiscountCurve,
                                        forDiscountCurve,
                                        model)

            vega = barrierOption.vega(valuation_date,
                                      spotFXRate,
                                      domDiscountCurve,
                                      forDiscountCurve,
                                      model)

            theta = barrierOption.theta(valuation_date,
                                        spotFXRate,
                                        domDiscountCurve,
                                        forDiscountCurve,
                                        model)

            testCases.print(optionType,
                            K,
                            B,
                            spotFXRate,
                            value,
                            delta,
                            vega,
                            theta)

###############################################################################

test_FinFXBarrierOption()
testCases.compareTestCases()
