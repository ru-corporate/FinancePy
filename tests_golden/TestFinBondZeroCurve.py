###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

import os
import datetime as dt

from financepy.utils.frequency import FrequencyTypes
from financepy.utils.day_count import DayCountTypes
from financepy.utils.date import Date, fromDatetime
from financepy.products.bonds.bond import Bond
from financepy.products.bonds.zero_curve import BondZeroCurve

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

plotGraphs = False

###############################################################################


def test_BondZeroCurve():

    import pandas as pd
    path = os.path.join(os.path.dirname(__file__), './data/giltBondPrices.txt')
    bondDataFrame = pd.read_csv(path, sep='\t')
    bondDataFrame['mid'] = 0.5*(bondDataFrame['bid'] + bondDataFrame['ask'])

    freq_type = FrequencyTypes.SEMI_ANNUAL
    accrual_type = DayCountTypes.ACT_ACT_ICMA
    settlement = Date(19, 9, 2012)

    bonds = []
    clean_prices = []

    for _, bondRow in bondDataFrame.iterrows():
        dateString = bondRow['maturity']
        matDatetime = dt.datetime.strptime(dateString, '%d-%b-%y')
        maturityDt = fromDatetime(matDatetime)
        issueDt = Date(maturityDt._d, maturityDt._m, 2000)
        coupon = bondRow['coupon']/100.0
        clean_price = bondRow['mid']
        bond = Bond(issueDt, maturityDt, coupon, freq_type, accrual_type)
        bonds.append(bond)
        clean_prices.append(clean_price)

###############################################################################

    bondCurve = BondZeroCurve(settlement, bonds, clean_prices)

    testCases.header("DATE", "ZERO RATE")

    for _, bond in bondDataFrame.iterrows():

        dateString = bond['maturity']
        matDatetime = dt.datetime.strptime(dateString, '%d-%b-%y')
        maturityDt = fromDatetime(matDatetime)
        zeroRate = bondCurve.zeroRate(maturityDt)
        testCases.print(maturityDt, zeroRate)

    if plotGraphs:
        bondCurve.plot("BOND CURVE")

###############################################################################


test_BondZeroCurve()
testCases.compareTestCases()
