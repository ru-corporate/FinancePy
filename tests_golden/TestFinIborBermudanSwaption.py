###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.global_types import FinSwapTypes
from financepy.utils.global_types import FinExerciseTypes
from financepy.products.rates.FinIborSwaption import FinIborSwaption
from financepy.products.rates.IborSwap import FinIborSwap

from financepy.products.rates.FinIborBermudanSwaption import FinIborBermudanSwaption
from financepy.models.black import FinModelBlack
from financepy.models.rates_bk_tree import FinModelRatesBK
from financepy.models.rates_hull_white_tree import FinModelRatesHW
from financepy.models.rates_bdt_tree import FinModelRatesBDT
from financepy.market.discount.curve_flat import DiscountCurveFlat

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinIborBermudanSwaptionBKModel():
    """ Replicate examples in paper by Leif Andersen which can be found at
    file:///C:/Users/Dominic/Downloads/SSRN-id155208.pdf """

    valuation_date = Date(1, 1, 2011)
    settlement_date = valuation_date
    exerciseDate = settlement_date.addYears(1)
    swapMaturityDate = settlement_date.addYears(4)

    swapFixedCoupon = 0.060
    swapFixedFrequencyType = FrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = DayCountTypes.ACT_365F

    libor_curve = DiscountCurveFlat(valuation_date,
                                    0.0625,
                                    FrequencyTypes.SEMI_ANNUAL,
                                    DayCountTypes.ACT_365F)

    fwdPAYSwap = FinIborSwap(exerciseDate,
                                swapMaturityDate,
                                FinSwapTypes.PAY,
                                swapFixedCoupon,
                                swapFixedFrequencyType,
                                swapFixedDayCountType)

    fwdSwapValue = fwdPAYSwap.value(settlement_date, libor_curve, libor_curve)

    testCases.header("LABEL", "VALUE")
    testCases.print("FWD SWAP VALUE", fwdSwapValue)

    # fwdPAYSwap.printFixedLegPV()

    # Now we create the European swaptions
    fixed_legType = FinSwapTypes.PAY
    europeanSwaptionPay = FinIborSwaption(settlement_date,
                                           exerciseDate,
                                           swapMaturityDate,
                                           fixed_legType,
                                           swapFixedCoupon,
                                           swapFixedFrequencyType,
                                           swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    europeanSwaptionRec = FinIborSwaption(settlement_date,
                                           exerciseDate,
                                           swapMaturityDate,
                                           fixed_legType,
                                           swapFixedCoupon,
                                           swapFixedFrequencyType,
                                           swapFixedDayCountType)
    
    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BLACK'S MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("======= ZERO VOLATILITY ========")
    model = FinModelBlack(0.0000001)
    testCases.print("Black Model", model._volatility)

    valuePay = europeanSwaptionPay.value(settlement_date, libor_curve, model)
    testCases.print("EUROPEAN BLACK PAY VALUE ZERO VOL:", valuePay)

    valueRec = europeanSwaptionRec.value(settlement_date, libor_curve, model)
    testCases.print("EUROPEAN BLACK REC VALUE ZERO VOL:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20%% BLACK VOLATILITY ========")

    model = FinModelBlack(0.20)
    testCases.print("Black Model", model._volatility)

    valuePay = europeanSwaptionPay.value(settlement_date, libor_curve, model)
    testCases.print("EUROPEAN BLACK PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(settlement_date, libor_curve, model)
    testCases.print("EUROPEAN BLACK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BK MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("=======================================================")
    testCases.banner("=======================================================")
    testCases.banner("==================== BK MODEL =========================")
    testCases.banner("=======================================================")
    testCases.banner("=======================================================")

    testCases.banner("======= 0% VOLATILITY EUROPEAN SWAPTION BK MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.000000001
    a = 0.01
    numTimeSteps = 100
    model = FinModelRatesBK(sigma, a, numTimeSteps)

    valuePay = europeanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BK PAY VALUE:", valuePay)
    
    valueRec = europeanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BK REC VALUE:", valueRec)
    
    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)


    testCases.banner("======= 20% VOLATILITY EUROPEAN SWAPTION BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = FinModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL SWAPTION CLASS EUROPEAN EXERCISE")

    valuePay = europeanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BK PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################

    # Now we create the Bermudan swaptions but only allow European exercise
    fixed_legType = FinSwapTypes.PAY
    exerciseType = FinExerciseTypes.EUROPEAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    exerciseType = FinExerciseTypes.EUROPEAN

    bermudanSwaptionRec = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)
   
    testCases.banner("======= 0% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = FinModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.2
    a = 0.01
    model = FinModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    # Now we create the Bermudan swaptions but allow Bermudan exercise
    ###########################################################################

    fixed_legType = FinSwapTypes.PAY
    exerciseType = FinExerciseTypes.BERMUDAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    exerciseType = FinExerciseTypes.BERMUDAN

    bermudanSwaptionRec = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    testCases.banner("======= ZERO VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = FinModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = FinModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BDT MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("=======================================================")
    testCases.banner("=======================================================")
    testCases.banner("======================= BDT MODEL =====================")
    testCases.banner("=======================================================")
    testCases.banner("=======================================================")

    testCases.banner("====== 0% VOLATILITY EUROPEAN SWAPTION BDT MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.00001
    numTimeSteps = 200
    model = FinModelRatesBDT(sigma, numTimeSteps)

    valuePay = europeanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BDT PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("===== 20% VOLATILITY EUROPEAN SWAPTION BDT MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = FinModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BDT MODEL SWAPTION CLASS EUROPEAN EXERCISE")

    valuePay = europeanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BDT PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    ###########################################################################

    # Now we create the Bermudan swaptions but only allow European exercise
    fixed_legType = FinSwapTypes.PAY
    exerciseType = FinExerciseTypes.EUROPEAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)
   
    testCases.banner("======= 0% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    model = FinModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.2
    model = FinModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BDT MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    # Now we create the Bermudan swaptions but allow Bermudan exercise
    ###########################################################################

    fixed_legType = FinSwapTypes.PAY
    exerciseType = FinExerciseTypes.BERMUDAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    testCases.banner("======= ZERO VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = FinModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = FinModelRatesBDT(sigma, numTimeSteps)

#    print("BDT MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BDT MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("=======================================================")
    testCases.banner("=======================================================")
    testCases.banner("======================= HW MODEL ======================")
    testCases.banner("=======================================================")
    testCases.banner("=======================================================")

    testCases.banner("====== 0% VOLATILITY EUROPEAN SWAPTION HW MODEL ======")

    sigma = 0.0000001
    a = 0.1
    numTimeSteps = 200
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    valuePay = europeanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN HW PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("===== 20% VOLATILITY EUROPEAN SWAPTION BDT MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.01
    a = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("HW MODEL SWAPTION CLASS EUROPEAN EXERCISE")

    valuePay = europeanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN HW PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("EUROPEAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    ###########################################################################

    # Now we create the Bermudan swaptions but only allow European exercise
    fixed_legType = FinSwapTypes.PAY
    exerciseType = FinExerciseTypes.EUROPEAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)
   
    testCases.banner("======= 0% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE HW MODEL ========")

    sigma = 0.000001
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 100bp VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE HW MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("BDT MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    # Now we create the Bermudan swaptions but allow Bermudan exercise
    ###########################################################################

    fixed_legType = FinSwapTypes.PAY
    exerciseType = FinExerciseTypes.BERMUDAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixed_legType = FinSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlement_date,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixed_legType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    testCases.banner("======= ZERO VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE HW MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("HW MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN HW PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 100bps VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE HW MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.01
    a = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("HW MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN HW PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuation_date, libor_curve, model)
    testCases.print("BERMUDAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
##########################################################################


test_FinIborBermudanSwaptionBKModel()

testCases.compareTestCases()
