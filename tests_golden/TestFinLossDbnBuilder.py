###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import matplotlib.pyplot as plt
import numpy as np
import time

import sys
sys.path.append("..")

from financepy.models.credit_gaussian_copula_onefactor import lossDbnRecursionGCD
from financepy.models.credit_gaussian_copula_onefactor import lossDbnHeterogeneousAdjBinomial

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

plotGraphs = False

##########################################################################


def test_FinLossDbnBuilder():

    num_credits = 125

    x = np.linspace(0, num_credits, num_credits + 1)
    defaultProb = 0.30
    num_steps = 25
    lossUnits = np.ones(num_credits)
    lossRatio = np.ones(num_credits)

    testCases.header(
        "BETA",
        "BUILDER",
        "LOSS0",
        "LOSS1",
        "LOSS2",
        "LOSS3",
        "TIME")

    for beta in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:

        defaultProbs = np.ones(num_credits) * defaultProb
        betaVector = np.ones(num_credits) * beta

        start = time.time()

        dbn1 = lossDbnRecursionGCD(num_credits,
                                   defaultProbs,
                                   lossUnits,
                                   betaVector,
                                   num_steps)

        end = time.time()

        testCases.print(
            beta,
            "FULL_GCD",
            dbn1[0],
            dbn1[1],
            dbn1[2],
            dbn1[3],
            end - start)

        #######################################################################

        start = time.time()
        dbn2 = lossDbnHeterogeneousAdjBinomial(num_credits,
                                               defaultProbs,
                                               lossRatio,
                                               betaVector,
                                               num_steps)
        end = time.time()

        testCases.print(
            beta,
            "ADJ_BIN",
            dbn2[0],
            dbn2[1],
            dbn2[2],
            dbn2[3],
            end - start)

        #######################################################################

        if plotGraphs:
            plt.figure()
            plt.plot(x, dbn1, label='GCD FULL')
            plt.plot(x, dbn2, label='ADJ BIN')
            plt.legend()
            plt.show()

            dbn3 = dbn2 - dbn1
            plt.plot(x, dbn3, label='DIFF')
            plt.legend()
            plt.show()

    #######################################################################
    # INHOMOGENEOUS CASE
    #######################################################################

    num_credits = 100
    beta = 0.0
    defaultProb = 0.10

    defaultProbs = np.random.randint(3, 4, size=(num_credits)) / 10.0
    betaVector = np.random.randint(5, 6, size=(num_credits)) / 10.0
    lossUnits = np.random.randint(1, 3, size=(num_credits)) / 1.0

    start = time.time()
    dbn1 = lossDbnRecursionGCD(num_credits,
                               defaultProbs,
                               lossUnits,
                               betaVector,
                               num_steps)
    end = time.time()

    testCases.print(
        beta,
        "ADJ_BIN",
        dbn1[0],
        dbn1[1],
        dbn1[2],
        dbn1[3],
        end - start)

    start = time.time()
    dbn2 = lossDbnHeterogeneousAdjBinomial(num_credits,
                                           defaultProbs,
                                           lossRatio,
                                           betaVector,
                                           num_steps)
    end = time.time()

    testCases.print(
        beta,
        "ADJ_BIN",
        dbn2[0],
        dbn2[1],
        dbn2[2],
        dbn2[3],
        end - start)

##########################################################################


test_FinLossDbnBuilder()
testCases.compareTestCases()
