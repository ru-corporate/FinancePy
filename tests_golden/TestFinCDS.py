###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import time
import numpy as np

import sys
sys.path.append("..")

from financepy.products.credit.cds import FinCDS
from financepy.utils.math import ONE_MILLION
from financepy.market.discount.interpolator import FinInterpTypes
from financepy.products.rates.IborSwap import FinIborSwap
from financepy.products.rates.FinIborDeposit import FinIborDeposit
from financepy.market.discount.curve import DiscountCurve
from financepy.products.rates.FinIborSingleCurve import IborSingleCurve
from financepy.products.credit.cds_curve import FinCDSCurve
from financepy.utils.global_vars import gDaysInYear
from financepy.utils.calendar import BusDayAdjustTypes
from financepy.utils.calendar import DateGenRuleTypes
from financepy.utils.calendar import CalendarTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.day_count import DayCountTypes
from financepy.utils.date import Date
from financepy.utils.global_types import FinSwapTypes

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

##########################################################################
# TO DO
##########################################################################


def test_CDSFastApproximation():

    valuation_date = Date(20, 6, 2018)
    # I build a discount curve that requires no bootstrap
    times = np.linspace(0, 10.0, 11)
    r = 0.05

    discount_factors = np.power((1.0 + r), -times)
    dates = valuation_date.addYears(times)

    libor_curve = DiscountCurve(valuation_date,
                                dates,
                                discount_factors,
                                FinInterpTypes.FLAT_FWD_RATES)

    ##########################################################################

    maturity_date = valuation_date.nextCDSDate(120)
    t = (maturity_date - valuation_date) / 365.242
    z = libor_curve.df(maturity_date)
    r = -np.log(z) / t

    recovery_rate = 0.40

    contractCoupon = 0.010

    testCases.header("MKT_SPD", "EXACT_VALUE", "APPROX_VALUE", "DIFF(%NOT)")

    for mktCoupon in np.linspace(0.000, 0.05, 21):

        cds_contracts = []

        cdsMkt = FinCDS(valuation_date, maturity_date, mktCoupon, ONE_MILLION)

        cds_contracts.append(cdsMkt)

        issuer_curve = FinCDSCurve(valuation_date,
                                  cds_contracts,
                                  libor_curve,
                                  recovery_rate)

        cds_contract = FinCDS(valuation_date, maturity_date, contractCoupon)
        v_exact = cds_contract.value(
            valuation_date, issuer_curve, recovery_rate)['full_pv']
        v_approx = cds_contract.valueFastApprox(
            valuation_date, r, mktCoupon, recovery_rate)[0]
        pctdiff = (v_exact - v_approx) / ONE_MILLION * 100.0
        testCases.print(mktCoupon * 10000, v_exact, v_approx, pctdiff)

##########################################################################


def test_CDSCurveRepricing():

    valuation_date = Date(20, 6, 2018)
    recovery_rate = 0.40

    cds_contracts, issuer_curve = test_IssuerCurveBuild()
    testCases.header("CDS_MATURITY_DATE", "PAR_SPREAD")
    for cds in cds_contracts:
        spd = cds.parSpread(valuation_date, issuer_curve, recovery_rate)
        testCases.print(str(cds._maturity_date), spd * 10000.0)

##########################################################################


def test_CDSCurveBuildTiming():

    numCurves = 1000

    start = time.time()
    for _ in range(0, numCurves):
        test_IssuerCurveBuild()

    end = time.time()

    testCases.header("LABEL", "TIME")
    duration = (end - start) / numCurves
    testCases.print(str(numCurves) + " Libor discount", duration)

##########################################################################


def test_IssuerCurveBuild():
    """ Test issuer curve build with simple libor curve to isolate cds
    curve building time cost. """

    valuation_date = Date(20, 6, 2018)

    times = np.linspace(0.0, 10.0, 11)
    r = 0.05
    discount_factors = np.power((1.0 + r), -times)
    dates = valuation_date.addYears(times)
    libor_curve = DiscountCurve(valuation_date,
                                dates,
                                discount_factors,
                                FinInterpTypes.FLAT_FWD_RATES)
    recovery_rate = 0.40

    cds_contracts = []

    cdsCoupon = 0.005  # 50 bps
    maturity_date = valuation_date.addMonths(12)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cds_contracts.append(cds)

    cdsCoupon = 0.0055
    maturity_date = valuation_date.addMonths(24)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cds_contracts.append(cds)

    cdsCoupon = 0.0060
    maturity_date = valuation_date.addMonths(36)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cds_contracts.append(cds)

    cdsCoupon = 0.0065
    maturity_date = valuation_date.addMonths(60)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cds_contracts.append(cds)

    cdsCoupon = 0.0070
    maturity_date = valuation_date.addMonths(84)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cds_contracts.append(cds)

    cdsCoupon = 0.0073
    maturity_date = valuation_date.addMonths(120)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cds_contracts.append(cds)

    issuer_curve = FinCDSCurve(valuation_date,
                              cds_contracts,
                              libor_curve,
                              recovery_rate)

    return cds_contracts, issuer_curve

##########################################################################


def buildFullIssuerCurve1(mktSpreadBump, irBump):

    # https://www.markit.com/markit.jsp?jsppage=pv.jsp
    # YIELD CURVE 8-AUG-2019 SNAP AT 1600

    tradeDate = Date(9, 8, 2019)
    valuation_date = tradeDate.addDays(1)

    m = 1.0  # 0.00000000000

    dcType = DayCountTypes.ACT_360
    depos = []
    depo1 = FinIborDeposit(valuation_date, "1D", m * 0.0220, dcType)
    depos.append(depo1)

    spotDays = 2
    settlement_date = valuation_date.addDays(spotDays)

    maturity_date = settlement_date.addMonths(1)
    depo1 = FinIborDeposit(settlement_date, maturity_date, m * 0.022009, dcType)

    maturity_date = settlement_date.addMonths(2)
    depo2 = FinIborDeposit(settlement_date, maturity_date, m * 0.022138, dcType)

    maturity_date = settlement_date.addMonths(3)
    depo3 = FinIborDeposit(settlement_date, maturity_date, m * 0.021810, dcType)

    maturity_date = settlement_date.addMonths(6)
    depo4 = FinIborDeposit(settlement_date, maturity_date, m * 0.020503, dcType)

    maturity_date = settlement_date.addMonths(12)
    depo5 = FinIborDeposit(settlement_date, maturity_date, m * 0.019930, dcType)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)
    depos.append(depo4)
    depos.append(depo5)

    fras = []

    swaps = []
    dcType = DayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = FrequencyTypes.SEMI_ANNUAL

    maturity_date = settlement_date.addMonths(24)
    swap1 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.015910 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturity_date = settlement_date.addMonths(36)
    swap2 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.014990 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturity_date = settlement_date.addMonths(48)
    swap3 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.014725 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturity_date = settlement_date.addMonths(60)
    swap4 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.014640 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    maturity_date = settlement_date.addMonths(72)
    swap5 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.014800 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap5)

    maturity_date = settlement_date.addMonths(84)
    swap6 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.014995 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap6)

    maturity_date = settlement_date.addMonths(96)
    swap7 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.015180 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap7)

    maturity_date = settlement_date.addMonths(108)
    swap8 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.015610 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap8)

    maturity_date = settlement_date.addMonths(120)
    swap9 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.015880 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap9)

    maturity_date = settlement_date.addMonths(144)
    swap10 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.016430 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap10)

    libor_curve = IborSingleCurve(valuation_date, depos, fras, swaps)

    cdsMarketContracts = []

    cdsCoupon = 0.04 + mktSpreadBump

    maturity_date = valuation_date.nextCDSDate(6)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(12)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(24)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(36)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(48)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(60)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(84)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(120)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturity_date = valuation_date.nextCDSDate(180)
    cds = FinCDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    recovery_rate = 0.40

    issuer_curve = FinCDSCurve(valuation_date,
                              cdsMarketContracts,
                              libor_curve,
                              recovery_rate)

    return libor_curve, issuer_curve

##########################################################################


def test_full_priceCDS1():

    mktSpread = 0.040

    testCases.header("Example", "Markit 9 Aug 2019")

    libor_curve, issuer_curve = buildFullIssuerCurve1(0.0, 0.0)

    # This is the 10 year contract at an off market coupon
    maturity_date = Date(20, 6, 2029)
    cdsCoupon = 0.0150
    notional = ONE_MILLION
    long_protection = True
    tradeDate = Date(9, 8, 2019)
    valuation_date = tradeDate.addDays(1)
    effective_date = valuation_date

    cds_contract = FinCDS(effective_date,
                         maturity_date,
                         cdsCoupon,
                         notional,
                         long_protection)

    cdsRecovery = 0.40

    testCases.header("LABEL", "VALUE")
    spd = cds_contract.parSpread(
        valuation_date,
        issuer_curve,
        cdsRecovery) * 10000.0
    testCases.print("PAR_SPREAD", spd)

    v = cds_contract.value(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("FULL_VALUE", v['full_pv'])
    testCases.print("CLEAN_VALUE", v['clean_pv'])

    p = cds_contract.clean_price(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("CLEAN_PRICE", p)

    # MARKIT PRICE IS 168517
    
    accrued_days = cds_contract.accrued_days()
    testCases.print("ACCRUED_DAYS", accrued_days)

    accruedInterest = cds_contract.accruedInterest()
    testCases.print("ACCRUED_COUPON", accruedInterest)

    prot_pv = cds_contract.protectionLegPV(
        valuation_date, issuer_curve, cdsRecovery)
    testCases.print("PROTECTION_PV", prot_pv)

    premPV = cds_contract.premiumLegPV(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("PREMIUM_PV", premPV)

    fullRPV01, cleanRPV01 = cds_contract.riskyPV01(valuation_date, issuer_curve)
    testCases.print("FULL_RPV01", fullRPV01)
    testCases.print("CLEAN_RPV01", cleanRPV01)

    # cds_contract.printFlows(issuer_curve)

    bump = 1.0 / 10000.0  # 1 bp

    libor_curve, issuer_curve = buildFullIssuerCurve1(bump, 0)
    v_bump = cds_contract.value(valuation_date, issuer_curve, cdsRecovery)
    dv = v_bump['full_pv'] - v['full_pv']
    testCases.print("CREDIT_DV01", dv)

    # Interest Rate Bump
    libor_curve, issuer_curve = buildFullIssuerCurve1(0, bump)
    v_bump = cds_contract.value(valuation_date, issuer_curve, cdsRecovery)
    dv = v_bump['full_pv'] - v['full_pv']
    testCases.print("INTEREST_DV01", dv)

    t = (maturity_date - valuation_date) / gDaysInYear
    z = libor_curve.df(maturity_date)
    r = -np.log(z) / t

    v_approx = cds_contract.valueFastApprox(valuation_date,
                                           r,
                                           mktSpread,
                                           cdsRecovery)

    testCases.print("FULL APPROX VALUE", v_approx[0])
    testCases.print("CLEAN APPROX VALUE", v_approx[1])
    testCases.print("APPROX CREDIT DV01", v_approx[2])
    testCases.print("APPROX INTEREST DV01", v_approx[3])

##########################################################################


def buildFullIssuerCurve2(mktSpreadBump, irBump):

    # https://www.markit.com/markit.jsp?jsppage=pv.jsp
    # YIELD CURVE 20 August 2020 SNAP AT 1600

    m = 1.0

    valuation_date = Date(24, 8, 2020)
    settlement_date = Date(24, 8, 2020)
    dcType = DayCountTypes.ACT_360
    depos = []

    maturity_date = settlement_date.addMonths(1)
    depo1 = FinIborDeposit(settlement_date, maturity_date, m * 0.001709, dcType)

    maturity_date = settlement_date.addMonths(2)
    depo2 = FinIborDeposit(settlement_date, maturity_date, m * 0.002123, dcType)

    maturity_date = settlement_date.addMonths(3)
    depo3 = FinIborDeposit(settlement_date, maturity_date, m * 0.002469, dcType)

    maturity_date = settlement_date.addMonths(6)
    depo4 = FinIborDeposit(settlement_date, maturity_date, m * 0.003045, dcType)

    maturity_date = settlement_date.addMonths(12)
    depo5 = FinIborDeposit(settlement_date, maturity_date, m * 0.004449, dcType)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)
    depos.append(depo4)
    depos.append(depo5)

    swaps = []
    dcType = DayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = FrequencyTypes.SEMI_ANNUAL

    maturity_date = settlement_date.addMonths(24)
    swap1 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.002155 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturity_date = settlement_date.addMonths(36)
    swap2 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.002305 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturity_date = settlement_date.addMonths(48)
    swap3 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.002665 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturity_date = settlement_date.addMonths(60)
    swap4 = FinIborSwap(
        settlement_date,
        maturity_date,
        FinSwapTypes.PAY,
        m * 0.003290 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    libor_curve = IborSingleCurve(valuation_date, depos, [], swaps)

    cdsCoupon = 0.01 + mktSpreadBump

    cdsMarketContracts = []
    effective_date = Date(21, 8, 2020)
    cds = FinCDS(effective_date, "6M", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "1Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "2Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "3Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "4Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "5Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "7Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = FinCDS(effective_date, "10Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    recovery_rate = 0.40

    issuer_curve = FinCDSCurve(settlement_date,
                              cdsMarketContracts,
                              libor_curve,
                              recovery_rate)

    testCases.header("DATE", "DISCOUNT_FACTOR", "SURV_PROB")
    years = np.linspace(0.0, 10.0, 20)
    dates = settlement_date.addYears(years)
    for dt in dates:
        df = libor_curve.df(dt)
        q = issuer_curve.survProb(dt)
        testCases.print("%16s" % dt, "%12.8f" % df, "%12.8f" % q)

    return libor_curve, issuer_curve

##########################################################################


def test_full_priceCDSModelCheck():

    testCases.print("Example", "MARKIT CHECK 19 Aug 2020")

    libor_curve, issuer_curve = buildFullIssuerCurve2(0.0, 0.0)

    # This is the 10 year contract at an off market coupon
    maturity_date = Date(20, 6, 2025)
    cdsCoupon = 0.050
    notional = ONE_MILLION
    long_protection = True
    tradeDate = Date(20, 8, 2020)
    effective_date = Date(21, 8, 2020)
    valuation_date = tradeDate

    cds_contract = FinCDS(effective_date,
                         maturity_date,
                         cdsCoupon,
                         notional,
                         long_protection)

    cdsRecovery = 0.40

    testCases.header("LABEL", "VALUE")
    spd = cds_contract.parSpread(
        valuation_date,
        issuer_curve,
        cdsRecovery) * 10000.0
    testCases.print("PAR_SPREAD", spd)

    v = cds_contract.value(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("FULL_VALUE", v['full_pv'])
    testCases.print("CLEAN_VALUE", v['clean_pv'])

    p = cds_contract.clean_price(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("CLEAN_PRICE", p)

    accrued_days = cds_contract.accrued_days()
    testCases.print("ACCRUED_DAYS", accrued_days)

    accruedInterest = cds_contract.accruedInterest()
    testCases.print("ACCRUED_COUPON", accruedInterest)

    prot_pv = cds_contract.protectionLegPV(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("PROTECTION_PV", prot_pv)

    premPV = cds_contract.premiumLegPV(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("PREMIUM_PV", premPV)

    rpv01 = cds_contract.riskyPV01(valuation_date, issuer_curve)
    testCases.print("FULL_RPV01", rpv01['full_rpv01'])
    testCases.print("CLEAN_RPV01", rpv01['clean_rpv01'])

    creditDV01 = cds_contract.creditDV01(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("CREDIT DV01", creditDV01)

    interestDV01 = cds_contract.interestDV01(valuation_date, issuer_curve, cdsRecovery)
    testCases.print("INTEREST DV01", interestDV01)

    # Consider fast approximation
    t = (maturity_date - valuation_date) / gDaysInYear
    z = libor_curve.df(maturity_date)
    r = -np.log(z) / t

    mktSpread = 0.01
    v_approx = cds_contract.valueFastApprox(valuation_date,
                                           r,
                                           mktSpread,
                                           cdsRecovery)

    testCases.header("FAST VALUATIONS", "VALUE")

    testCases.print("FULL APPROX VALUE", v_approx[0])
    testCases.print("CLEAN APPROX VALUE", v_approx[1])
    testCases.print("APPROX CREDIT DV01", v_approx[2])
    testCases.print("APPROX INTEREST DV01", v_approx[3])

##########################################################################


def test_full_priceCDSConvergence():

    _, issuer_curve = buildFullIssuerCurve1(0.0, 0.0)

    # This is the 10 year contract at an off market coupon
    maturity_date = Date(20, 6, 2029)
    cdsCoupon = 0.0150
    notional = ONE_MILLION
    long_protection = False
    tradeDate = Date(9, 8, 2019)
    valuation_date = tradeDate.addDays(1)

    cds_contract = FinCDS(valuation_date,
                         maturity_date,
                         cdsCoupon,
                         notional,
                         long_protection)

    cdsRecovery = 0.40

    testCases.header("NumSteps", "Value")
    for n in [10, 50, 100, 500, 1000]:
        v_full = cds_contract.value(
            valuation_date, issuer_curve, cdsRecovery, 0, 1, n)['full_pv']
        testCases.print(n, v_full)

##########################################################################


def test_CDSDateGeneration():

    # This is the 10 year contract at an off market coupon
    maturity_date = Date(20, 6, 2029)
    cdsCoupon = 0.0100

    tradeDate = Date(9, 8, 2019)
    valuation_date = tradeDate.addDays(1)

    cds_contract = FinCDS(valuation_date,
                         maturity_date,
                         cdsCoupon,
                         ONE_MILLION,
                         True,
                         FrequencyTypes.QUARTERLY,
                         DayCountTypes.ACT_360,
                         CalendarTypes.WEEKEND,
                         BusDayAdjustTypes.FOLLOWING,
                         DateGenRuleTypes.BACKWARD)

    testCases.header("Flow Date", "AccrualFactor", "Flow")
    num_flows = len(cds_contract._adjusted_dates)
    for n in range(0, num_flows):
        testCases.print(str(
            cds_contract._adjusted_dates[n]), cds_contract._accrual_factors[n],
            cds_contract._flows[n])

##########################################################################



test_CDSCurveBuildTiming()
test_full_priceCDSModelCheck()
test_CDSDateGeneration()
test_full_priceCDS1()
test_full_priceCDSConvergence()
test_CDSCurveRepricing()
test_CDSFastApproximation()

testCases.compareTestCases()
