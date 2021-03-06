##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

from ...finutils.FinError import FinError
from ...finutils.Date import Date
from ...finutils.FinGlobalVariables import gSmall
from ...finutils.FinDayCount import FinDayCount, DayCountTypes
from ...finutils.FinFrequency import FrequencyTypes, FinFrequency
from ...finutils.FinCalendar import CalendarTypes,  DateGenRuleTypes
from ...finutils.FinCalendar import FinCalendar, BusDayAdjustTypes
from ...finutils.FinSchedule import FinSchedule
from ...finutils.FinHelperFunctions import labelToString, check_argument_types
from ...finutils.FinMath import ONE_MILLION
from ...finutils.FinGlobalTypes import FinSwapTypes
from ...market.curves.FinDiscountCurve import FinDiscountCurve

##########################################################################


class FinIborSwapOLD(object):
    """ Class for managing a Fixed vs IBOR swap contract. This is a contract
    in which a fixed payment leg is exchanged for a series of floating rates
    payments linked to some IBOR index rate. There is no exchange of par.
    The contract is entered into at zero initial cost. The contract lasts from
    a start date to a specified maturity date.

    The floating rate is not known fully until the end of the preceding payment
    period. It is set in advance and paid in arrears. 
    
    The value of the contract is the NPV of the two coupon streams. Discounting
    is done on a supplied discount curve which is separate from the curve from
    which the implied index rates are extracted. """
    
    def __init__(self,
                 effective_date: Date,  # Date interest starts to accrue
                 termination_date_or_tenor: (Date, str),  # Date contract ends
                 fixed_legType: FinSwapTypes,
                 fixedCoupon: float,  # Fixed coupon (annualised)
                 fixedFreqType: FrequencyTypes,
                 fixedDayCountType: DayCountTypes,
                 notional: float = ONE_MILLION,
                 floatSpread: float = 0.0,
                 floatFreqType: FrequencyTypes = FrequencyTypes.QUARTERLY,
                 floatDayCountType: DayCountTypes = DayCountTypes.THIRTY_E_360,
                 calendar_type: CalendarTypes = CalendarTypes.WEEKEND,
                 bus_day_adjust_type: BusDayAdjustTypes = BusDayAdjustTypes.FOLLOWING,
                 date_gen_rule_type: DateGenRuleTypes = DateGenRuleTypes.BACKWARD):
        """ Create an interest rate swap contract giving the contract start
        date, its maturity, fixed coupon, fixed leg frequency, fixed leg day
        count convention and notional. The floating leg parameters have default
        values that can be overwritten if needed. The start date is contractual
        and is the same as the settlement date for a new swap. It is the date
        on which interest starts to accrue. The end of the contract is the
        termination date. This is not adjusted for business days. The adjusted
        termination date is called the maturity date. This is calculated. """

        check_argument_types(self.__init__, locals())

        if type(termination_date_or_tenor) == Date:
            self._termination_date = termination_date_or_tenor
        else:
            self._termination_date = effective_date.addTenor(termination_date_or_tenor)

        calendar = Calendar(calendar_type)
        self._maturity_date = calendar.adjust(self._termination_date,
                                             bus_day_adjust_type)

        if effective_date > self._maturity_date:
            raise FinError("Start date after maturity date")

        self._effective_date = effective_date
        self._notional = notional

        self._fixedCoupon = fixedCoupon
        self._floatSpread = floatSpread

        self._fixedFrequencyType = fixedFreqType
        self._floatFrequencyType = floatFreqType

        self._fixedDayCountType = fixedDayCountType
        self._floatDayCountType = floatDayCountType

        self._fixed_legType = fixed_legType

        self._calendar_type = calendar_type
        self._bus_day_adjust_type = bus_day_adjust_type
        self._date_gen_rule_type = date_gen_rule_type

        # These are generated immediately as they are for the entire
        # life of the swap. Given a valuation date we can determine
        # which cash flows are in the future and value the swap
        self._generateFixedLegPaymentDates()
        self._generateFloatLegPaymentDates()

        self._adjustedMaturityDate = self._adjustedFixedDates[-1]

        # Need to know latest payment date for bootstrap - DO I NEED THIS ??!
        self._lastPaymentDate = self._maturity_date
        if self._adjustedFixedDates[-1] > self._lastPaymentDate:
            self._lastPaymentDate = self._adjustedFixedDates[-1]

        if self._adjustedFloatDates[-1] > self._lastPaymentDate:
            self._lastPaymentDate = self._adjustedFloatDates[-1]

        # NOT TO BE PRINTED
        self._floatYearFracs = []
        self._floatFlows = []
        self._floatFlowPVs = []
        self._floatDfs = []

        self._fixedYearFracs = []
        self._fixedFlows = []
        self._fixedDfs = []
        self._fixedFlowPVs = []

        self._firstFixingRate = None
        self._valuation_date = None
        self._fixedStartIndex = None

        self._calcFixedLegFlows()

###############################################################################

    def _calcFixedLegFlows(self):

        self._fixedYearFracs = []
        self._fixedFlows = []

        day_counter = FinDayCount(self._fixedDayCountType)

        """ Now PV fixed leg flows. """
        prevDt = self._adjustedFixedDates[0]

        for nextDt in self._adjustedFixedDates[1:]:
            alpha = day_counter.year_frac(prevDt, nextDt)[0]
            flow = self._fixedCoupon * alpha * self._notional
            prevDt = nextDt
            self._fixedYearFracs.append(alpha)
            self._fixedFlows.append(flow)
            
###############################################################################

    def value(self,
              valuation_date: Date,
              discount_curve: FinDiscountCurve,
              index_curve: FinDiscountCurve=None,
              firstFixingRate=None,
              principal=0.0):
        """ Value the interest rate swap on a value date given a single Ibor
        discount curve. """

        if index_curve is None:
            index_curve = discount_curve

        fixed_legValue = self.fixed_legValue(valuation_date,
                                           discount_curve,
                                           principal)

        floatLegValue = self.floatLegValue(valuation_date,
                                           discount_curve,
                                           index_curve,
                                           firstFixingRate,
                                           principal)

        value = fixed_legValue - floatLegValue

        if self._fixed_legType == FinSwapTypes.PAY:
            value = value * (-1.0)

        return value

##########################################################################

    def _generateFixedLegPaymentDates(self):
        """ Generate the fixed leg payment dates all the way back to
        the start date of the swap which may precede the valuation date"""
        self._adjustedFixedDates = FinSchedule(
            self._effective_date,
            self._termination_date,
            self._fixedFrequencyType,
            self._calendar_type,
            self._bus_day_adjust_type,
            self._date_gen_rule_type)._generate()

##########################################################################

    def _generateFloatLegPaymentDates(self):
        """ Generate the floating leg payment dates all the way back to
        the start date of the swap which may precede the valuation date"""
        self._adjustedFloatDates = FinSchedule(
            self._effective_date,
            self._termination_date,
            self._floatFrequencyType,
            self._calendar_type,
            self._bus_day_adjust_type,
            self._date_gen_rule_type)._generate()

##########################################################################

    def pv01(self, valuation_date, discount_curve):
        """ Calculate the value of 1 basis point coupon on the fixed leg. """

        pv = self.fixed_legValue(valuation_date, discount_curve)
        pv01 = pv / self._fixedCoupon / self._notional
        return pv01

##########################################################################

    def swap_rate(self,
                 valuation_date:Date,
                 discount_curve: FinDiscountCurve,
                 index_curve: FinDiscountCurve = None,
                 firstFixing: float = None):
        """ Calculate the fixed leg coupon that makes the swap worth zero.
        If the valuation date is before the swap payments start then this
        is the forward swap rate as it starts in the future. The swap rate
        is then a forward swap rate and so we use a forward discount
        factor. If the swap fixed leg has begun then we have a spot
        starting swap. The swap rate can also be calculated in a dual curve 
        approach but in this case the first fixing on the floating leg is
        needed. """

        pv01 = self.pv01(valuation_date, discount_curve)

        if abs(pv01) < gSmall:
            raise FinError("PV01 is zero. Cannot compute swap rate.")

        if valuation_date < self._effective_date:
            df0 = discount_curve.df(self._effective_date)
        else:
            df0 = discount_curve.df(valuation_date)

        floatLegPV = 0.0

        if index_curve is None:
            dfT = discount_curve.df(self._maturity_date)
            floatLegPV = (df0 - dfT) 
        else:
            floatLegPV = self.floatLegValue(valuation_date,
                                            discount_curve,
                                            index_curve,
                                            firstFixing)
            floatLegPV /= self._notional

        cpn = floatLegPV / pv01           
        return cpn
    
##########################################################################

    def fixed_legValue(self,
                      valuation_date: Date,
                      discount_curve: FinDiscountCurve,
                      principal: float =0.0):

        self._valuation_date = valuation_date

        self._fixedYearFracs = []
        self._fixedFlows = []
        self._fixedDfs = []
        self._fixedFlowPVs = []
        self._fixedTotalPV = []

        day_counter = FinDayCount(self._fixedDayCountType)

        """ The swap may have started in the past but we can only value
        payments that have occurred after the valuation date. """
        start_index = 0
        while self._adjustedFixedDates[start_index] < valuation_date:
            start_index += 1

        """ If the swap has yet to settle then we do not include the
        start date of the swap as a coupon payment date. """
        if valuation_date <= self._effective_date:
            start_index = 1

        self._fixedStartIndex = start_index

        """ Now PV fixed leg flows. """
        self._dfValuationDate = discount_curve.df(valuation_date)

        pv = 0.0
        prevDt = self._adjustedFixedDates[start_index - 1]
        df_discount = 1.0
        if len(self._adjustedFixedDates) == 1:
            return 0.0

        for nextDt in self._adjustedFixedDates[start_index:]:
            alpha = day_counter.year_frac(prevDt, nextDt)[0]
            df_discount = discount_curve.df(nextDt) / self._dfValuationDate
            flow = self._fixedCoupon * alpha * self._notional
            flowPV = flow * df_discount
            pv += flowPV
            prevDt = nextDt
            self._fixedYearFracs.append(alpha)
            self._fixedFlows.append(flow)
            self._fixedDfs.append(df_discount)
            self._fixedFlowPVs.append(flow * df_discount)
            self._fixedTotalPV.append(pv)

        flow = principal * self._notional
        flowPV = flow * df_discount
        pv += flowPV
        self._fixedFlowPVs[-1] += flowPV
        self._fixedFlows[-1] += flow
        self._fixedTotalPV[-1] = pv
        return pv

##########################################################################

    def cashSettledPV01(self,
                        valuation_date,
                        flatSwapRate,
                        freq_type):
        """ Calculate the forward value of an annuity of a forward starting
        swap using a single flat discount rate equal to the swap rate. This is
        used in the pricing of a cash-settled swaption in the FinIborSwaption
        class. This method does not affect the standard valuation methods."""

        m = FinFrequency(freq_type)

        if m == 0:
            raise FinError("Frequency cannot be zero.")

        """ The swap may have started in the past but we can only value
        payments that have occurred after the valuation date. """
        start_index = 0
        while self._adjustedFixedDates[start_index] < valuation_date:
            start_index += 1

        """ If the swap has yet to settle then we do not include the
        start date of the swap as a coupon payment date. """
        if valuation_date <= self._effective_date:
            start_index = 1

        """ Now PV fixed leg flows. """
        flatPV01 = 0.0
        df = 1.0
        alpha = 1.0 / m

        for _ in self._adjustedFixedDates[start_index:]:
            df = df / (1.0 + alpha * flatSwapRate)
            flatPV01 += df * alpha

        return flatPV01

##########################################################################

    def floatLegValue(self,
                      valuation_date: Date,  # This should be the settlement date
                      discount_curve: FinDiscountCurve,
                      index_curve: FinDiscountCurve,
                      firstFixingRate: float=None,
                      principal: float=0.0):
        """ Value the floating leg with payments from an index curve and
        discounting based on a supplied discount curve. The valuation date can
        be the today date. In this case the price of the floating leg will not
        be par (assuming we added on a principal repayment). This is only the
        case if we set the valuation date to be the swap's actual settlement
        date. """

        self._valuation_date = valuation_date
        self._floatYearFracs = []
        self._floatFlows = []
        self._floatRates = []
        self._floatDfs = []
        self._floatFlowPVs = []
        self._floatTotalPV = []
        self._firstFixingRate = firstFixingRate

        basis = FinDayCount(self._floatDayCountType)

        """ The swap may have started in the past but we can only value
        payments that have occurred after the start date. """
        start_index = 0
        while self._adjustedFloatDates[start_index] < valuation_date:
            start_index += 1

        """ If the swap has yet to settle then we do not include the
        start date of the swap as a coupon payment date. """
        if valuation_date <= self._effective_date:
            start_index = 1

        self._floatStartIndex = start_index

        # Forward price to settlement date (if valuation is settlement date)
        self._dfValuationDate = discount_curve.df(valuation_date)

        """ The first floating payment is usually already fixed so is
        not implied by the index curve. """
        prevDt = self._adjustedFloatDates[start_index - 1]
        nextDt = self._adjustedFloatDates[start_index]
        alpha = basis.year_frac(prevDt, nextDt)[0]

        if self._firstFixingRate is None and self._effective_date < valuation_date:
            raise FinError("First fixing rate has to be set.")

        if self._firstFixingRate is None:
            df1_index = index_curve.df(self._effective_date)  # Cannot be pcd as has past
            df2_index = index_curve.df(nextDt)
            fwdIndexRate = (df1_index / df2_index - 1.0) / alpha
            flow = (fwdIndexRate + self._floatSpread) * alpha * self._notional
        else:
            fwdIndexRate = self._firstFixingRate
            flow = (fwdIndexRate + self._floatSpread) * alpha * self._notional

        # All discounting is done forward to the valuation date
        df_discount = discount_curve.df(nextDt) / self._dfValuationDate

        pv = flow * df_discount

        self._floatYearFracs.append(alpha)
        self._floatFlows.append(flow)
        self._floatRates.append(fwdIndexRate)
        self._floatDfs.append(df_discount)
        self._floatFlowPVs.append(flow * df_discount)
        self._floatTotalPV.append(pv)

        prevDt = nextDt
        df1_index = index_curve.df(prevDt)

        for nextDt in self._adjustedFloatDates[start_index + 1:]:
            alpha = basis.year_frac(prevDt, nextDt)[0]
            df2_index = index_curve.df(nextDt)
            # The accrual factors cancel
            fwdIndexRate = (df1_index / df2_index - 1.0) / alpha
            flow = (fwdIndexRate + self._floatSpread) * alpha * self._notional

            # All discounting is done forward to the valuation date
            df_discount = discount_curve.df(nextDt) / self._dfValuationDate

            pv += flow * df_discount
            df1_index = df2_index
            prevDt = nextDt

            self._floatFlows.append(flow)
            self._floatYearFracs.append(alpha)
            self._floatRates.append(fwdIndexRate)
            self._floatDfs.append(df_discount)
            self._floatFlowPVs.append(flow * df_discount)
            self._floatTotalPV.append(pv)

        flow = principal * self._notional
        pv = pv + flow * df_discount
        self._floatFlows[-1] += flow
        self._floatFlowPVs[-1] += flow * df_discount
        self._floatTotalPV[-1] = pv

        return pv

##########################################################################

    def printFixedLegPV(self):
        """ Prints the fixed leg dates, accrual factors, discount factors,
        cash amounts, their present value and their cumulative PV using the
        last valuation performed. """

        print("START DATE:", self._effective_date)
        print("MATURITY DATE:", self._maturity_date)
        print("COUPON (%):", self._fixedCoupon * 100)
        print("FIXED LEG FREQUENCY:", str(self._fixedFrequencyType))
        print("FIXED LEG DAY COUNT:", str(self._fixedDayCountType))
        print("VALUATION DATE", self._valuation_date)

        if len(self._fixedFlows) == 0:
            print("Fixed Flows not calculated.")
            return

        header = "PAYMENT_DATE     YEAR_FRAC        FLOW         DF"
        header += "         DF*FLOW       CUM_PV"
        print(header)

        if self._fixedStartIndex is None:
            raise FinError("Need to value swap before calling this function.")

        start_index = 1 # TODO CHECK

        # By definition the discount factor is 1.0 on the valuation date
        print("%15s %10s %12s %12.8f %12s %12s" %
              (self._valuation_date, "-", "-", 1.0, "-", "-"))

        iFlow = 0
        for payment_date in self._adjustedFixedDates[start_index:]:
            print("%15s %10.7f %12.2f %12.8f %12.2f %12.2f" %
                  (payment_date,
                   self._fixedYearFracs[iFlow],
                   self._fixedFlows[iFlow],
                   self._fixedDfs[iFlow],
                   self._fixedFlowPVs[iFlow],
                   self._fixedTotalPV[iFlow]))

            iFlow += 1

###############################################################################

    def printFixedLegFlows(self):
        """ Prints the fixed leg amounts without any valuation details. Shows
        the dates and sizes of the promised fixed leg flows. """

        print("START DATE:", self._effective_date)
        print("MATURITY DATE:", self._maturity_date)
        print("COUPON (%):", self._fixedCoupon * 100)
        print("FIXED LEG FREQUENCY:", str(self._fixedFrequencyType))
        print("FIXED LEG DAY COUNT:", str(self._fixedDayCountType))

        if len(self._fixedFlows) == 0:
            print("Fixed Flows not calculated.")
            return

        header = "PAYMENT_DATE     YEAR_FRAC        FLOW"
        print(header)

        # As we have no valuation date, we print them all.
        start_index = 0

        iFlow = 0
        for payment_date in self._adjustedFixedDates[start_index:]:
            print("%15s %12.8f %12.2f" %
                  (payment_date,
                   self._fixedYearFracs[iFlow],
                   self._fixedFlows[iFlow]))

            iFlow += 1

###############################################################################

    def printFloatLegFlows(self):
        """ Prints the float leg amounts without any valuation details. Shows
        the dates and sizes of the promised float leg flows. """

        print("START DATE:", self._effective_date)
        print("MATURITY DATE:", self._maturity_date)
        print("FLOAT SPREAD (bps):", self._floatSpread * 10000)
        print("FLOAT LEG FREQUENCY:", str(self._floatFrequencyType))
        print("FLOAT LEG DAY COUNT:", str(self._floatDayCountType))

        header = "PAYMENT_DATE     YEAR_FRAC        FLOW"
        print(header)

        start_index = self._floatStartIndex
        iFlow = 0
        for payment_date in self._adjustedFloatDates[start_index:]:
            print("%15s %12.8f        N/A" %
                  (payment_date, self._floatYearFracs[iFlow]))

            iFlow += 1

###############################################################################

    def printFloatLegPV(self):
        """ Prints the floating leg dates, accrual factors, discount factors,
        forward libor rates, implied cash amounts, their present value and
        their cumulative PV using the last valuation performed. """

        print("START DATE:", self._effective_date)
        print("MATURITY DATE:", self._maturity_date)
        print("SPREAD COUPON (%):", self._floatSpread * 100)
        print("FLOAT LEG FREQUENCY:", str(self._floatFrequencyType))
        print("FLOAT LEG DAY COUNT:", str(self._floatDayCountType))
        print("VALUATION DATE", self._valuation_date)

        if len(self._floatFlows) == 0:
            print("Floating Flows not calculated.")
            return

        if self._firstFixingRate is None:
            print("         *** FIRST FLOATING RATE PAYMENT IS IMPLIED ***")

        header = "PAYMENT_DATE     YEAR_FRAC    RATE(%)       FLOW         DF"
        header += "         DF*FLOW       CUM_PV"
        print(header)

        start_index = self._floatStartIndex

        # By definition the discount factor is 1.0 on the valuation date

        print("%15s %10s %10s %12s %12.8f %12s %12s" %
              (self._valuation_date,
               "-",
               "-",
               "-",
               1.0,
               "-",
               "-"))

        iFlow = 0
        for payment_date in self._adjustedFloatDates[start_index:]:
            print("%15s %10.7f %10.5f %12.2f %12.8f %12.2f %12.2f" %
                  (payment_date,
                   self._floatYearFracs[iFlow],
                   self._floatRates[iFlow]*100.0,
                   self._floatFlows[iFlow],
                   self._floatDfs[iFlow],
                   self._floatFlowPVs[iFlow],
                   self._floatTotalPV[iFlow]))

            iFlow += 1

##########################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("START DATE", self._effective_date)
        s += labelToString("TERMINATION DATE", self._termination_date)
        s += labelToString("MATURITY DATE", self._maturity_date)
        s += labelToString("NOTIONAL", self._notional)
        s += labelToString("FIXED LEG TYPE", self._fixed_legType)
        s += labelToString("FIXED COUPON", self._fixedCoupon)
        s += labelToString("FLOAT SPREAD", self._floatSpread)
        s += labelToString("FIXED FREQUENCY", self._fixedFrequencyType)
        s += labelToString("FLOAT FREQUENCY", self._floatFrequencyType)
        s += labelToString("FIXED DAY COUNT", self._fixedDayCountType)
        s += labelToString("FLOAT DAY COUNT", self._floatDayCountType)
        s += labelToString("CALENDAR", self._calendar_type)
        s += labelToString("BUS DAY ADJUST", self._bus_day_adjust_type)
        s += labelToString("DATE GEN TYPE", self._date_gen_rule_type)
        return s

###############################################################################

    def _print(self):
        """ Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. """
        print(self)

###############################################################################
