# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 16:23:12 2019

@author: Dominic
"""

import time
import numpy as np

from FinTestCases import FinTestCases, globalTestCaseMode

from financepy.finutils.FinDate import FinDate
from financepy.finutils.FinDayCount import FinDayCountTypes
from financepy.finutils.FinFrequency import FinFrequencyTypes

from financepy.products.libor.FinLiborDeposit import FinLiborDeposit
from financepy.products.libor.FinLiborSwap import FinLiborSwap
from financepy.products.libor.FinLiborSwaption import FinLiborSwaption
from financepy.products.libor.FinLiborSwaption import FinLiborSwaptionTypes

from financepy.models.FinModelBlack import FinModelBlack
from financepy.models.FinModelBlackShifted import FinModelBlackShifted
from financepy.models.FinModelSABR import FinModelSABR
from financepy.models.FinModelSABRShifted import FinModelSABRShifted
from financepy.models.FinModelRatesHW import FinModelRatesHW

from financepy.finutils.FinCalendar import *

from financepy.market.curves.FinLiborCurve import FinLiborCurve
from financepy.market.curves.FinFlatCurve import FinFlatCurve
from financepy.market.curves.FinZeroCurve import FinZeroCurve
from financepy.market.curves.FinInterpolate import FinInterpMethods

testCases = FinTestCases(__file__, globalTestCaseMode)


def test_FinLiborDepositsAndSwaps(valuationDate):

    depoBasis = FinDayCountTypes.THIRTY_E_360_ISDA
    depos = []

    spotDays = 0
    settlementDate = valuationDate.addWorkDays(spotDays)
    depositRate = 0.05

    depo1 = FinLiborDeposit(settlementDate, "1M", depositRate, depoBasis)
    depo2 = FinLiborDeposit(settlementDate, "3M", depositRate, depoBasis)
    depo3 = FinLiborDeposit(settlementDate, "6M", depositRate, depoBasis)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)

    fras = []

    swaps = []
    fixedBasis = FinDayCountTypes.ACT_365_ISDA
    fixedFreq = FinFrequencyTypes.SEMI_ANNUAL

    swapRate = 0.05
    swap1 = FinLiborSwap(settlementDate, "1Y", swapRate, fixedFreq, fixedBasis)
    swap2 = FinLiborSwap(settlementDate, "3Y", swapRate, fixedFreq, fixedBasis)
    swap3 = FinLiborSwap(settlementDate, "5Y", swapRate, fixedFreq, fixedBasis)

    swaps.append(swap1)
    swaps.append(swap2)
    swaps.append(swap3)

    liborCurve = FinLiborCurve("USD_LIBOR", settlementDate, depos, fras, swaps)

    return liborCurve


##########################################################################

def testFinLiborSwaptionModels():

    ##########################################################################
    # COMPARISON OF MODELS
    ##########################################################################

    valuationDate = FinDate(2011, 1, 1)
    liborCurve = test_FinLiborDepositsAndSwaps(valuationDate)

    exerciseDate = FinDate(2012, 1, 1)
    swapMaturityDate = FinDate(2017, 1, 1)

    swapFixedFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = FinDayCountTypes.ACT_365_ISDA

    strikes = np.linspace(0.02, 0.08, 10)

    print("LABEL", "STRIKE", "BLK", "BLK_SHFTD", "SABR", "SABR_SHFTD", "HW")

    model1 = FinModelBlack(0.00001)
    model2 = FinModelBlackShifted(0.00001, 0.0)
    model3 = FinModelSABR(0.013, 0.5, 0.5, 0.5)
    model4 = FinModelSABRShifted(0.013, 0.5, 0.5, 0.5, -0.008)
    model5 = FinModelRatesHW(0.00001, 0.00001)

    settlementDate = valuationDate.addWorkDays(2)

    for k in strikes:
        swaptionType = FinLiborSwaptionTypes.PAYER
        swaption = FinLiborSwaption(settlementDate,
                                    exerciseDate,
                                    swapMaturityDate,
                                    swaptionType,
                                    k,
                                    swapFixedFrequencyType,
                                    swapFixedDayCountType)

        swap1 = swaption.value(valuationDate, liborCurve, model1)
        swap2 = swaption.value(valuationDate, liborCurve, model2)
        swap3 = swaption.value(valuationDate, liborCurve, model3)
        swap4 = swaption.value(valuationDate, liborCurve, model4)
        swap5 = swaption.value(valuationDate, liborCurve, model5)
        print("PAY", swap1, swap2, swap3, swap4, swap5)

    print("LABEL", "STRIKE", "BLK", "BLK_SHFTD", "SABR", "SABR_SHFTD", "HW")

    for k in strikes:
        swaptionType = FinLiborSwaptionTypes.RECEIVER
        swaption = FinLiborSwaption(settlementDate,
                                    exerciseDate,
                                    swapMaturityDate,
                                    swaptionType,
                                    k,
                                    swapFixedFrequencyType,
                                    swapFixedDayCountType)

        swap1 = swaption.value(valuationDate, liborCurve, model1)
        swap2 = swaption.value(valuationDate, liborCurve, model2)
        swap3 = swaption.value(valuationDate, liborCurve, model3)
        swap4 = swaption.value(valuationDate, liborCurve, model4)
        swap5 = swaption.value(valuationDate, liborCurve, model5)
        print("REC", k, swap1, swap2, swap3, swap4, swap5)

###############################################################################


def test_FinLiborSwaptionQLExample():

    valuationDate = FinDate(28, 2, 2014)
    settlementDate = FinDate(4, 3, 2014)

    depoDCCType = FinDayCountTypes.THIRTY_E_360_ISDA
    depos = []
    depo = FinLiborDeposit(settlementDate, "1W", 0.0023, depoDCCType)
    depos.append(depo)
    depo = FinLiborDeposit(settlementDate, "1M", 0.0023, depoDCCType)
    depos.append(depo)
    depo = FinLiborDeposit(settlementDate, "3M", 0.0023, depoDCCType)
    depos.append(depo)
    depo = FinLiborDeposit(settlementDate, "6M", 0.0023, depoDCCType)
    depos.append(depo)

    # No convexity correction provided so I omit interest rate futures

    swaps = []
    accType = FinDayCountTypes.ACT_365_ISDA
    fixedFreqType = FinFrequencyTypes.SEMI_ANNUAL

    swap = FinLiborSwap(settlementDate, "3Y", 0.00790, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "4Y", 0.01200, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "5Y", 0.01570, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "6Y", 0.01865, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "7Y", 0.02160, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "8Y", 0.02350, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "9Y", 0.02540, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "10Y", 0.0273, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "15Y", 0.0297, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "20Y", 0.0316, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "25Y", 0.0335, fixedFreqType, accType)
    swaps.append(swap)
    swap = FinLiborSwap(settlementDate, "30Y", 0.0354, fixedFreqType, accType)
    swaps.append(swap)

    liborCurve = FinLiborCurve("USD_LIBOR", valuationDate, depos, [], swaps,
                               FinInterpMethods.LINEAR_ZERO_RATES)

    exerciseDate = settlementDate.addTenor("5Y")
    swapMaturityDate = exerciseDate.addTenor("5Y")
    swapFixedCoupon = 0.040852
    swapFixedFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    swapFloatFrequencyType = FinFrequencyTypes.QUARTERLY
    swapFloatDayCountType = FinDayCountTypes.ACT_360
    swapNotional = 1000000
    swaptionType = FinLiborSwaptionTypes.PAYER

    swaption = FinLiborSwaption(settlementDate,
                                exerciseDate,
                                swapMaturityDate,
                                swaptionType,
                                swapFixedCoupon,
                                swapFixedFrequencyType,
                                swapFixedDayCountType,
                                swapNotional,
                                swapFloatFrequencyType,
                                swapFloatDayCountType)

    model = FinModelBlack(0.1533)
    v = swaption.value(settlementDate, liborCurve, model)
    print(v)

    model = FinModelBlackShifted(0.1533, -0.008)
    v = swaption.value(settlementDate, liborCurve, model)
    print(v)

    model = FinModelSABR(0.132, 0.5, 0.5, 0.5)
    v = swaption.value(settlementDate, liborCurve, model)
    print(v)

    model = FinModelSABRShifted(0.352, 0.5, 0.15, 0.15, -0.005)
    v = swaption.value(settlementDate, liborCurve, model)
    print(v)

    model = FinModelRatesHW(0.010000000, 0.00000000001)
    v = swaption.value(settlementDate, liborCurve, model)
    print(v)
    print(swaption)

###############################################################################


def testFinLiborSwaptionMatlabExamples():

    # We value a European swaption using Black's model and try to replicate a
    # ML example at https://fr.mathworks.com/help/fininst/swaptionbyblk.html

    print("=======================================")
    print("MATLAB EXAMPLE WITH FLAT TERM STRUCTURE")
    print("=======================================")

    valuationDate = FinDate(1, 1, 2010)
    liborCurve = FinFlatCurve(valuationDate, 0.06, -1)

    settlementDate = FinDate(1, 1, 2011)
    exerciseDate = FinDate(1, 1, 2016)
    maturityDate = FinDate(1, 1, 2019)

    fixedCoupon = 0.062
    fixedFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    floatFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    notional = 100.0

    # Pricing a PAYER
    swaptionType = FinLiborSwaptionTypes.PAYER
    swaption = FinLiborSwaption(settlementDate,
                                exerciseDate,
                                maturityDate,
                                swaptionType,
                                fixedCoupon,
                                fixedFrequencyType,
                                fixedDayCountType,
                                notional,
                                floatFrequencyType,
                                floatDayCountType)

    model = FinModelBlack(0.20)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 2.071

    print("FP Price:", v_finpy)
    print("MATLAB Prix:", v_matlab)
    print("DIFF:", v_finpy - v_matlab)
    print(swaption)

###############################################################################

    print("===================================")
    print("MATLAB EXAMPLE WITH TERM STRUCTURE")
    print("===================================")

    valuationDate = FinDate(1, 1, 2010)

    dates = [FinDate(1, 1, 2011), FinDate(1, 1, 2012), FinDate(1, 1, 2013),
             FinDate(1, 1, 2014), FinDate(1, 1, 2015)]

    zeroRates = [0.03, 0.034, 0.037, 0.039, 0.040]

    contFreq = FinFrequencyTypes.CONTINUOUS
    interpMethod = FinInterpMethods.LINEAR_ZERO_RATES
    dayCountType = FinDayCountTypes.ACT_ACT_ISDA

    liborCurve = FinZeroCurve(valuationDate, dates, zeroRates, contFreq,
                              dayCountType, interpMethod)

    settlementDate = FinDate(1, 1, 2011)
    exerciseDate = FinDate(1, 1, 2012)
    maturityDate = FinDate(1, 1, 2017)
    fixedCoupon = 0.03

    fixedFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    floatFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    notional = 1000.0

    # Pricing a PAYER
    swaptionType = FinLiborSwaptionTypes.RECEIVER
    swaption = FinLiborSwaption(settlementDate,
                                exerciseDate,
                                maturityDate,
                                swaptionType,
                                fixedCoupon,
                                fixedFrequencyType,
                                fixedDayCountType,
                                notional,
                                floatFrequencyType,
                                floatDayCountType)

    model = FinModelBlack(0.21)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 0.5771

    print("FP Price:", v_finpy)
    print("MATLAB Prix:", v_matlab)
    print("DIFF:", v_finpy - v_matlab)

    print(swaption)

###############################################################################

    print("===================================")
    print("MATLAB EXAMPLE WITH SHIFTED BLACK")
    print("===================================")

    valuationDate = FinDate(1, 1, 2016)

    dates = [FinDate(1, 1, 2017), FinDate(1, 1, 2018), FinDate(1, 1, 2019),
             FinDate(1, 1, 2020), FinDate(1, 1, 2021)]

    zeroRates = np.array([-0.02, 0.024, 0.047, 0.090, 0.12])/100.0

    contFreq = FinFrequencyTypes.ANNUAL
    interpMethod = FinInterpMethods.LINEAR_ZERO_RATES
    dayCountType = FinDayCountTypes.ACT_ACT_ISDA

    liborCurve = FinZeroCurve(valuationDate, dates, zeroRates, contFreq,
                              dayCountType, interpMethod)

    settlementDate = FinDate(1, 1, 2016)
    exerciseDate = FinDate(1, 1, 2017)
    maturityDate = FinDate(1, 1, 2020)
    fixedCoupon = -0.003

    fixedFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    floatFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    notional = 1000.0

    # Pricing a PAYER
    swaptionType = FinLiborSwaptionTypes.PAYER
    swaption = FinLiborSwaption(settlementDate,
                                exerciseDate,
                                maturityDate,
                                swaptionType,
                                fixedCoupon,
                                fixedFrequencyType,
                                fixedDayCountType,
                                notional,
                                floatFrequencyType,
                                floatDayCountType)

    model = FinModelBlackShifted(0.31, -0.008)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 12.8301

    print("FP Price:", v_finpy)
    print("MATLAB Prix:", v_matlab)
    print("DIFF:", v_finpy - v_matlab)

    print(swaption)


###############################################################################

    print("===================================")
    print("MATLAB EXAMPLE WITH HULL WHITE")
    print("===================================")

    # https://fr.mathworks.com/help/fininst/swaptionbyhw.html

    valuationDate = FinDate(1, 1, 2007)

    dates = [FinDate(1, 1, 2007), FinDate(1, 7, 2007), FinDate(1, 1, 2008),
             FinDate(1, 7, 2008), FinDate(1, 1, 2009), FinDate(1, 7, 2009),
             FinDate(1, 1, 2010), FinDate(1, 7, 2010),
             FinDate(1, 1, 2011), FinDate(1, 7, 2011), FinDate(1, 1, 2012)]

    zeroRates = np.array([0.075] * 11)
    interpMethod = FinInterpMethods.FLAT_FORWARDS
    dayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    contFreq = FinFrequencyTypes.SEMI_ANNUAL

    liborCurve = FinZeroCurve(valuationDate, dates, zeroRates, contFreq,
                              dayCountType, interpMethod)

    settlementDate = valuationDate
    exerciseDate = FinDate(1, 1, 2010)
    maturityDate = FinDate(1, 1, 2012)
    fixedCoupon = 0.04

    fixedFrequencyType = FinFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = FinDayCountTypes.THIRTY_E_360_ISDA
    notional = 100.0

    swaptionType = FinLiborSwaptionTypes.RECEIVER
    swaption = FinLiborSwaption(settlementDate,
                                exerciseDate,
                                maturityDate,
                                swaptionType,
                                fixedCoupon,
                                fixedFrequencyType,
                                fixedDayCountType,
                                notional)

    model = FinModelRatesHW(0.05, 0.01)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 2.9201

    print("FP Price:", v_finpy)
    print("MATLAB Prix:", v_matlab)
    print("DIFF:", v_finpy - v_matlab)

    print(swaption)
###############################################################################

# test_FinLiborSwaption()
# testFinLiborSwaptionModels()
testFinLiborSwaptionMatlabExamples()
# test_FinLiborSwaptionQLExample()
# testCases.compareTestCases()
