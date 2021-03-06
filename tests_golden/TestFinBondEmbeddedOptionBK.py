###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import matplotlib.pyplot as plt
import time

import sys
sys.path.append("..")

from financepy.utils.date import Date
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.day_count import DayCountTypes

from financepy.products.rates.IborSwap import FinIborSwap
from financepy.products.rates.FinIborDeposit import FinIborDeposit

from financepy.products.rates.FinIborSingleCurve import IborSingleCurve
from financepy.market.discount.curve_flat import DiscountCurveFlat
from financepy.products.bonds.bond import Bond
from financepy.products.bonds.bond_embedded_option import BondEmbeddedOption
from financepy.utils.global_types import FinSwapTypes

from financepy.models.rates_bk_tree import FinModelRatesBK

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

plotGraphs = False

###############################################################################


def test_BondEmbeddedOptionMATLAB():
    # https://fr.mathworks.com/help/fininst/optembndbybk.html
    # I FIND THAT THE PRICE CONVERGES TO 102.365 WHICH IS CLOSE TO 102.382
    # FOUND BY MATLAB ALTHOUGH THEY DO NOT EXAMINE THE ASYMPTOTIC PRICE
    # WHICH MIGHT BE A BETTER MATCH - ALSO THEY DO NOT USE A REALISTIC VOL

    valuation_date = Date(1, 1, 2007)
    settlement_date = valuation_date

    ###########################################################################

    fixed_legType = FinSwapTypes.PAY
    dcType = DayCountTypes.THIRTY_E_360
    fixedFreq = FrequencyTypes.ANNUAL
    swap1 = FinIborSwap(settlement_date, "1Y", fixed_legType, 0.0350, fixedFreq, dcType)
    swap2 = FinIborSwap(settlement_date, "2Y", fixed_legType, 0.0400, fixedFreq, dcType)
    swap3 = FinIborSwap(settlement_date, "3Y", fixed_legType, 0.0450, fixedFreq, dcType)
    swaps = [swap1, swap2, swap3]
    discount_curve = IborSingleCurve(valuation_date, [], [], swaps)

    ###########################################################################

    issue_date = Date(1, 1, 2005)
    maturity_date = Date(1, 1, 2010)
    coupon = 0.0525
    freq_type = FrequencyTypes.ANNUAL
    accrual_type = DayCountTypes.ACT_ACT_ICMA
    bond = Bond(issue_date, maturity_date, coupon, freq_type, accrual_type)

    call_dates = []
    call_prices = []
    put_dates = []
    put_prices = []

    putDate = Date(1, 1, 2008)
    for _ in range(0, 24):
        put_dates.append(putDate)
        put_prices.append(100)
        putDate = putDate.addMonths(1)

    testCases.header("BOND PRICE", "PRICE")
    v = bond.clean_price_from_discount_curve(settlement_date, discount_curve)
    testCases.print("Bond Pure Price:", v)

    sigma = 0.01  # This volatility is very small for a BK process
    a = 0.1

    puttableBond = BondEmbeddedOption(issue_date, maturity_date, coupon,
                                      freq_type, accrual_type,
                                      call_dates, call_prices,
                                      put_dates, put_prices)

    testCases.header("TIME", "NumTimeSteps", "BondWithOption", "BondPure")

    timeSteps = range(100, 200, 10)  # 1000, 10)
    values = []
    for numTimeSteps in timeSteps:
        model = FinModelRatesBK(sigma, a, numTimeSteps)
        start = time.time()
        v = puttableBond.value(settlement_date, discount_curve, model)
        end = time.time()
        period = end - start
        testCases.print(period, numTimeSteps, v['bondwithoption'],
                        v['bondpure'])

        values.append(v['bondwithoption'])

    if plotGraphs:
        plt.figure()
        plt.plot(timeSteps, values)

###############################################################################


def test_BondEmbeddedOptionQUANTLIB():

    # Based on example at the nice blog on Quantlib at
    # http://gouthamanbalaraman.com/blog/callable-bond-quantlib-python.html
    # I get a price of 68.97 for 1000 time steps which is higher than the
    # 68.38 found in blog article. But this is for 40 grid points.
    # Note also that a basis point vol of 0.120 is 12% which is VERY HIGH!

    valuation_date = Date(16, 8, 2016)
    settlement_date = valuation_date.addWeekDays(3)

    ###########################################################################

    discount_curve = DiscountCurveFlat(valuation_date, 0.035,
                                       FrequencyTypes.SEMI_ANNUAL)

    ###########################################################################

    issue_date = Date(15, 9, 2010)
    maturity_date = Date(15, 9, 2022)
    coupon = 0.025
    freq_type = FrequencyTypes.QUARTERLY
    accrual_type = DayCountTypes.ACT_ACT_ICMA
    bond = Bond(issue_date, maturity_date, coupon, freq_type, accrual_type)

    ###########################################################################
    # Set up the call and put times and prices
    ###########################################################################

    nextCallDate = Date(15, 9, 2016)
    call_dates = [nextCallDate]
    call_prices = [100.0]

    for _ in range(1, 24):
        nextCallDate = nextCallDate.addMonths(3)
        call_dates.append(nextCallDate)
        call_prices.append(100.0)

    put_dates = []
    put_prices = []

    # the value used in blog of 12% bp vol is unrealistic
    sigma = 0.12/0.035  # basis point volatility
    a = 0.03

    puttableBond = BondEmbeddedOption(issue_date, maturity_date, coupon,
                                      freq_type, accrual_type,
                                      call_dates, call_prices,
                                      put_dates, put_prices)

    testCases.header("BOND PRICE", "PRICE")
    v = bond.clean_price_from_discount_curve(settlement_date, discount_curve)
    testCases.print("Bond Pure Price:", v)

    testCases.header("TIME", "NumTimeSteps", "BondWithOption", "BondPure")
    timeSteps = range(100, 200, 20)  # 1000, 10)
    values = []
    for numTimeSteps in timeSteps:
        model = FinModelRatesBK(sigma, a, numTimeSteps)
        start = time.time()
        v = puttableBond.value(settlement_date, discount_curve, model)
        end = time.time()
        period = end - start
        testCases.print(period, numTimeSteps, v['bondwithoption'],
                        v['bondpure'])
        values.append(v['bondwithoption'])

    if plotGraphs:
        plt.figure()
        plt.title("Puttable Bond Price Convergence")
        plt.plot(timeSteps, values)

###############################################################################


test_BondEmbeddedOptionMATLAB()
test_BondEmbeddedOptionQUANTLIB()
testCases.compareTestCases()
