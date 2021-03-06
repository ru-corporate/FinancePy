###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import matplotlib.pyplot as plt
import numpy as np
import time as time

import sys
sys.path.append("..")

from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.calendar import CalendarTypes
from financepy.products.rates.FinIborFRA import FinIborFRA
from financepy.products.rates.FinIborFuture import FinIborFuture
from financepy.products.rates.FinIborDeposit import FinIborDeposit
from financepy.products.rates.IborSwap import FinIborSwap
from financepy.utils.calendar import BusDayAdjustTypes
from financepy.market.discount.interpolator import FinInterpTypes
from financepy.utils.math import ONE_MILLION
from financepy.utils.global_types import FinSwapTypes
from financepy.market.discount.interpolator import FinInterpTypes
from financepy.products.rates.FinIborSingleCurve import IborSingleCurve
from financepy.products.rates.FinIborDualCurve import IborDualCurve
from financepy.products.rates.FinOISCurve import OISCurve
from financepy.products.rates.FinOIS import FinOIS

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

PLOT_GRAPHS = False

###############################################################################

def buildOIS(valuation_date):
    """ Build the OIS funding curve from futures (FRAs) and OIS """

    dccType = DayCountTypes.THIRTY_E_360_ISDA
    depos = []

    spotDays = 0
    spotDays = 0
    settlement_date = valuation_date.addWeekDays(spotDays)
    fixed_legType = FinSwapTypes.PAY

    fras = []
    # 1 x 4 FRA
    
    swaps = []
    fixedFreqType = FrequencyTypes.SEMI_ANNUAL
    fixedDCCType = DayCountTypes.ACT_365F

    swap_rate = 0.000022
    maturity_date = settlement_date.addMonths(24)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                            fixedFreqType, fixedDCCType)
    swaps.append(swap)

    swap_rate += 0.000
    fixed_legType = FinSwapTypes.PAY
    maturity_date = settlement_date.addMonths(36)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType, fixedDCCType)
    swaps.append(swap)

    swap_rate += 0.000
    maturity_date = settlement_date.addMonths(48)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    swap_rate = 0.02
    maturity_date = settlement_date.addMonths(60)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                  fixedFreqType,
                  fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(72)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                       fixedFreqType,
                       fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(84)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(96)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(108)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(120)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(132)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(144)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(180)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(240)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(300)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    maturity_date = settlement_date.addMonths(360)
    swap = FinOIS(settlement_date, maturity_date, fixed_legType, swap_rate,
                        fixedFreqType,
                        fixedDCCType)
    swaps.append(swap)

    oisCurve = OISCurve(valuation_date,
                        [],
                        fras,
                        swaps)

    return oisCurve

###############################################################################


def test_bloombergPricingExample():

    """ This is an example of a replication of a BBG example from
    https://github.com/vilen22/curve-building/blob/master/Bloomberg%20Curve%20Building%20Replication.xlsx

    """
    valuation_date = Date(6, 6, 2018)

    # We do the O/N rate which settles on trade date
    spotDays = 0
    settlement_date = valuation_date.addWeekDays(spotDays)
    depoDCCType = DayCountTypes.ACT_360
    depos = []
    deposit_rate = 0.0231381
    maturity_date = settlement_date.addMonths(3)
    depo = FinIborDeposit(settlement_date, maturity_date, deposit_rate,
                           depoDCCType)
    depos.append(depo)

    futs = []
    fut = FinIborFuture(valuation_date, 1); futs.append(fut)
    fut = FinIborFuture(valuation_date, 2); futs.append(fut)
    fut = FinIborFuture(valuation_date, 3); futs.append(fut)
    fut = FinIborFuture(valuation_date, 4); futs.append(fut)
    fut = FinIborFuture(valuation_date, 5); futs.append(fut)
    fut = FinIborFuture(valuation_date, 6); futs.append(fut)

    fras = [None]*6
    fras[0] = futs[0].toFRA(97.6675, -0.00005)
    fras[1] = futs[1].toFRA(97.5200, -0.00060)
    fras[2] = futs[2].toFRA(97.3550, -0.00146)
    fras[3] = futs[3].toFRA(97.2450, -0.00263)
    fras[4] = futs[4].toFRA(97.1450, -0.00411)
    fras[5] = futs[5].toFRA(97.0750, -0.00589)

    accrual = DayCountTypes.THIRTY_E_360
    freq = FrequencyTypes.SEMI_ANNUAL

    spotDays = 2
    settlement_date = valuation_date.addWeekDays(spotDays)
    notional = ONE_MILLION
    fixed_legType = FinSwapTypes.PAY
    interp_type = FinInterpTypes.FLAT_FWD_RATES

    swaps = []
    swap = FinIborSwap(settlement_date, "2Y", fixed_legType, (2.77417+2.77844)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "3Y", fixed_legType, (2.86098+2.86582)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "4Y", fixed_legType, (2.90240+2.90620)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "5Y", fixed_legType, (2.92944+2.92906)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "6Y", fixed_legType, (2.94001+2.94499)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "7Y", fixed_legType, (2.95352+2.95998)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "8Y", fixed_legType, (2.96830+2.97400)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "9Y", fixed_legType, (2.98403+2.98817)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "10Y", fixed_legType, (2.99716+3.00394)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "11Y", fixed_legType, (3.01344+3.01596)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "12Y", fixed_legType, (3.02276+3.02684)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "15Y", fixed_legType, (3.04092+3.04508)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "20Y", fixed_legType, (3.04417+3.05183)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "25Y", fixed_legType, (3.03219+3.03621)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "30Y", fixed_legType, (3.01030+3.01370)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "40Y", fixed_legType, (2.96946+2.97354)/200, freq, accrual); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "50Y", fixed_legType, (2.91552+2.93748)/200, freq, accrual); swaps.append(swap)

    libor_curve = IborSingleCurve(valuation_date, depos, fras, swaps, interp_type, True)

    principal = 0.0
    testCases.banner("======================================================")
    testCases.banner("SINGLE CURVE VALUATION")
    testCases.header("LABEL", "VALUE")
    testCases.print("VALUE:", swaps[0].value(valuation_date, libor_curve, libor_curve, None))
    testCases.print("FIXED:", swaps[0]._fixed_leg.value(valuation_date, libor_curve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(valuation_date, libor_curve, libor_curve, None))

    testCases.banner("======================================================")
    testCases.banner("SINGLE CURVE VALUATION TO SWAP SETTLEMENT DATE")
    testCases.header("LABEL", "VALUE")
    testCases.print("VALUE:", swaps[0].value(settlement_date, libor_curve, libor_curve, None))
    testCases.print("FIXED:", swaps[0]._fixed_leg.value(settlement_date, libor_curve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(settlement_date, libor_curve, libor_curve, None))
    testCases.banner("======================================================")

#    swaps[0].printFixedLegPV()
#    swaps[0].printFloatLegPV()

    oisCurve = buildOIS(valuation_date)
#    print(oisCurve)

    liborDualCurve = IborDualCurve(valuation_date, oisCurve, depos, fras, swaps,
                                   FinInterpTypes.FLAT_FWD_RATES, True)
#    print(liborDualCurve) 
    
    # The valuation of 53714.55 is very close to the spreadsheet value 53713.96

    testCases.header("VALUATION TO TODAY DATE"," PV")
    testCases.print("VALUE:", swaps[0].value(valuation_date, oisCurve, liborDualCurve, None))
    testCases.print("FIXED:", swaps[0]._fixed_leg.value(valuation_date, oisCurve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(valuation_date, oisCurve, libor_curve, None))

    testCases.header("VALUATION TO SWAP SETTLEMENT DATE"," PV")
    testCases.print("VALUE:", swaps[0].value(settlement_date, oisCurve, liborDualCurve, None))
    testCases.print("FIXED:", swaps[0]._fixed_leg.value(settlement_date, oisCurve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(settlement_date, oisCurve, liborDualCurve, None, ))

#    swaps[0].printFixedLegPV()
#    swaps[0].printFloatLegPV()

    PLOT = False
    if PLOT is True:

        years = np.linspace(0, 5, 21)
        dates = settlement_date.addYears(years)
    
        singleCurveFwds = libor_curve.fwd(dates)
        plt.plot(years, singleCurveFwds, label="Single Libor Curve")
 
        oisCurveFwds = oisCurve.fwd(dates)    
        plt.plot(years, oisCurveFwds, label="OIS Curve")

        index_curveFwds = liborDualCurve.fwd(dates)
        plt.plot(years, index_curveFwds, label="Libor Index Curve")
        
        plt.legend()
    
    # swaps[0].printFixedLegPV()
    # swaps[0].printFloatLegPV()

###############################################################################

def test_swapValuationExample():
    
    # Example from
    # https://blog.deriscope.com/index.php/en/excel-interest-rate-swap-price-dual-bootstrapping-curve
    
    vBloomberg = 388147

    valuation_date = Date(30, 11, 2018)

    start_date = Date(27, 12, 2017)
    maturity_date = Date(27, 12, 2067)
    notional = 10 * ONE_MILLION
    fixed_legType = FinSwapTypes.RECEIVE
    
    fixedRate = 0.0150
    fixedDCCType = DayCountTypes.THIRTY_360_BOND
    fixedFreqType = FrequencyTypes.ANNUAL
    
    floatSpread = 0.0
    floatDCCType = DayCountTypes.ACT_360
    floatFreqType = FrequencyTypes.SEMI_ANNUAL

    offMarketSwap = FinIborSwap(start_date, maturity_date, fixed_legType,
                                fixedRate, fixedFreqType, fixedDCCType,
                                notional,
                                floatSpread, floatFreqType, floatDCCType)
    
    interp_type = FinInterpTypes.LINEAR_ZERO_RATES
    
    depoDCCType = DayCountTypes.ACT_360
    depos = []
    
    ###########################################################################
    # MARKET
    ###########################################################################
    
    spotDays = 0
    settlement_date = valuation_date.addWeekDays(spotDays)
    depo = FinIborDeposit(settlement_date, "6M", -0.2510/100.0, depoDCCType); depos.append(depo)
    
    fras = []
    fraDCCType = DayCountTypes.ACT_360
    
    fra = FinIborFRA(settlement_date.addTenor("1M"), "6M", -0.2450/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("2M"), "6M", -0.2435/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("3M"), "6M", -0.2400/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("4M"), "6M", -0.2360/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("5M"), "6M", -0.2285/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("6M"), "6M", -0.2230/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("7M"), "6M", -0.2110/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("8M"), "6M", -0.1990/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("9M"), "6M", -0.1850/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("10M"), "6M", -0.1680/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("11M"), "6M", -0.1510/100.0, fraDCCType); fras.append(fra)
    fra = FinIborFRA(settlement_date.addTenor("12M"), "6M", -0.1360/100.0, fraDCCType); fras.append(fra)
    
    swaps = []
    fixed_legType = FinSwapTypes.PAY
    fixedDCCType = DayCountTypes.THIRTY_360_BOND
    fixedFreqType = FrequencyTypes.ANNUAL
    
    swap = FinIborSwap(settlement_date, "2Y", fixed_legType, -0.1525/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "3Y", fixed_legType, -0.0185/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "4Y", fixed_legType, 0.1315/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "5Y", fixed_legType, 0.2745/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "6Y", fixed_legType, 0.4135/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "7Y", fixed_legType, 0.5439/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "8Y", fixed_legType, 0.6652/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "9Y", fixed_legType, 0.7784/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "10Y", fixed_legType, 0.8799/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "11Y", fixed_legType, 0.9715/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "12Y", fixed_legType, 1.0517/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "15Y", fixed_legType, 1.2369/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "20Y", fixed_legType, 1.3965/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "25Y", fixed_legType, 1.4472/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "30Y", fixed_legType, 1.4585/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "35Y", fixed_legType, 1.4595/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "40Y", fixed_legType, 1.4535/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "45Y", fixed_legType, 1.4410/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinIborSwap(settlement_date, "50Y", fixed_legType, 1.4335/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    
    iborDepos = depos.copy()
    iborFras = fras.copy()
    iborSwaps = swaps.copy()
    
    iborCurve = IborSingleCurve(valuation_date, iborDepos, iborFras, iborSwaps, interp_type)
    v1 = offMarketSwap.value(valuation_date, iborCurve, iborCurve, -0.268/100.0)    

    testCases.banner("DERISCOPE EXAMPLE REPLICATION")    
    testCases.header("LABEL", "VALUE")
    testCases.print("BBG VALUE", vBloomberg)
    testCases.print("FP ONE CURVE VALUE", v1)
    
    ###############################################################################
    
    depoDCCType = DayCountTypes.ACT_360
    depos = []
    
    spotDays = 0
    settlement_date = valuation_date.addWeekDays(spotDays)
    depo = FinIborDeposit(settlement_date, "1D", -0.3490/100.0, depoDCCType); depos.append(depo)
    
    fras = []
    
    swaps = []
    fixed_legType = FinSwapTypes.PAY
    fixedDCCType = DayCountTypes.ACT_365F
    fixedFreqType = FrequencyTypes.ANNUAL
    
    # Standard OIS with standard annual terms
    swap = FinOIS(settlement_date, "2W", fixed_legType, -0.3600/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "1M", fixed_legType, -0.3560/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "2M", fixed_legType, -0.3570/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "3M", fixed_legType, -0.3580/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "4M", fixed_legType, -0.3575/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "5M", fixed_legType, -0.3578/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "6M", fixed_legType, -0.3580/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "7M", fixed_legType, -0.3600/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "8M", fixed_legType, -0.3575/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "9M", fixed_legType, -0.3569/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "10M", fixed_legType, -0.3553/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "11M", fixed_legType, -0.3534/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "12M", fixed_legType, -0.3496/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "18M", fixed_legType, -0.3173/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    
    swap = FinOIS(settlement_date, "2Y", fixed_legType, -0.2671/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "30M", fixed_legType, -0.2070/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "3Y", fixed_legType, -0.1410/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "4Y", fixed_legType, -0.0060/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "5Y", fixed_legType, 0.1285/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "6Y", fixed_legType, 0.2590/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "7Y", fixed_legType, 0.3830/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "8Y", fixed_legType, 0.5020/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "9Y", fixed_legType, 0.6140/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "10Y", fixed_legType, 0.7160/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "11Y", fixed_legType, 0.8070/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "12Y", fixed_legType, 0.8890/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "15Y", fixed_legType, 1.0790/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "20Y", fixed_legType, 1.2460/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "25Y", fixed_legType, 1.3055/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "30Y", fixed_legType, 1.3270/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "35Y", fixed_legType, 1.3315/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "40Y", fixed_legType, 1.3300/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = FinOIS(settlement_date, "50Y", fixed_legType, 1.3270/100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    
    oisDepos = depos.copy()
    oisFras = fras.copy()
    oisSwaps = swaps.copy()
    
#    oisCurveFF = FinOISCurve(valuation_date, oisDepos, oisFras, oisSwaps, interp_type)
    
    iborDualCurve = IborDualCurve(valuation_date, oisCurveFF, iborDepos, iborFras, iborSwaps, interp_type)
    
#    v2 = offMarketSwap.value(valuation_date, oisCurveFF, iborDualCurve, -0.268/100.0)
    
#    testCases.print("FP DUAL CURVE VALUE", v2)

#    swap_rate = offMarketSwap.swap_rate(valuation_date, oisCurveFF, iborCurve, -0.268/100.0)

#    testCases.print("FP DUAL CURVE SWAP RATE", swap_rate)

#    offMarketSwap.printFixedLegFlows()
#    offMarketSwap.printFloatLegFlows()
#    offMarketSwap.printFixedLegPV()
#    offMarketSwap.printFloatLegPV()
    

###############################################################################

#test_swapValuationExample()

test_bloombergPricingExample()

testCases.compareTestCases()
