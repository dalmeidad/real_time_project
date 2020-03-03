#!/usr/bin/env python

"""
schedulability.py - suite of schedulability tests

Written by: Tanya Amert
"""

from taskset import TaskSetJsonKeys, Task

import matplotlib.pyplot as plt
import random

def getUniformValue(a, b):
    """
    Returns a value uniformly selected from the range [a,b].
    """
    return random.uniform(a,b)

# Per-task utilization functions
lightUtilFunc = lambda : getUniformValue(0.001, 0.01)
mediumLightUtilFunc = lambda : getUniformValue(0.01, 0.1)
mediumUtilFunc = lambda : getUniformValue(0.1, 0.4)

# periods are in milliseconds
shortPeriodFunc = lambda : getUniformValue(3, 33)
longPeriodFunc = lambda : getUniformValue(50, 250)
choicePeriodFunc = lambda : random.choice([250, 500, 750, 1000, 1500, 2000, 6000])

def generateRandomTaskSet(targetUtil, utilFunc, periodFunc):
    """
    Generates a random task set with total utilization targetUtil.

    Just returns the task set as a list of Task objects, rather than
    the proper TaskSet type.
    """
    utilSum = 0

    # Generate tasks until the utilization target is met
    taskSet = []
    i = 0
    while utilSum < targetUtil:
        taskId = i+1
        remaining_util = targetUtil - utilSum
        cur_util = utilFunc()
        if cur_util > remaining_util:
            cur_util = remaining_util
        utilSum += cur_util

        offset = 0 # critical section. OR getUniformValue(3, 250) -> low: min short period, high: max long period
        period = periodFunc()
        relativeDeadline = period # implicit-deadlines
        wcet = period * cur_util


        # TODO:
        # Choose the utilization for the task based on the utilization function
        # (you just need to call it - it already has its parameters figured out).
        # If the task's utilization would push it over the target, instead choose
        # its utilization to be the remaining utilization to reach the target sum.

        # Choose task parameters:
        # * offset
        # * period
        # * relative deadline
        # * WCET <-- choose based on utilization and period

        # Build the dictionary for the task parameters
        taskDict = {}
        taskDict[TaskSetJsonKeys.KEY_TASK_ID] = taskId
        taskDict[TaskSetJsonKeys.KEY_TASK_PERIOD] = period
        taskDict[TaskSetJsonKeys.KEY_TASK_WCET] = wcet
        taskDict[TaskSetJsonKeys.KEY_TASK_DEADLINE] = relativeDeadline
        taskDict[TaskSetJsonKeys.KEY_TASK_OFFSET] = offset

        task = Task(taskDict)
        taskSet.append(task)

    return taskSet

def rmSchedulabilityTest(taskSet):
    """
    Performs the simple utilization-based schedulability test for RM.

    Only checks the total utilization sum against the U_lub bound.
    Does not check per-task.
    """
    util_sum = 0
    num_tasks = len(taskSet)
    u_lub = num_tasks * (2 ** (1/num_tasks) - 1)
    for task in taskSet:
        util_sum += task.wcet / task.period
        if util_sum > u_lub:
            return False
    return True

def checkSchedulability(numTaskSets, targetUtilization, utilFunc, periodFunc, testFunc):
    """
    Generates numTaskSets task sets using a given utilization-generation function
    and a given period-generation function, such that the task sets have a given
    target system utilization.  Uses the given schedulability test to determine
    what fraction of the task sets are schedulable.

    Returns: the fraction of task sets that pass the schedulability test.
    """
    count = 0
    for i in range(numTaskSets):
        taskSet = generateRandomTaskSet(targetUtilization, utilFunc, periodFunc)

        if testFunc(taskSet):
            count += 1

    return count / numTaskSets

def performTests(numTests):
    utilizationVals = []
    for i in range(21):
        val = 0.65 + i * 0.01
        utilizationVals.append(val)

    results = {}
    results["light"] = []
    results["medlight"] = []
    results["medium"] = []

    for util in utilizationVals:
        lightResult = checkSchedulability(numTests, util, lightUtilFunc, shortPeriodFunc, rmSchedulabilityTest)
        medLightResult = checkSchedulability(numTests, util, mediumLightUtilFunc, shortPeriodFunc, rmSchedulabilityTest)
        mediumResult = checkSchedulability(numTests, util, mediumUtilFunc, shortPeriodFunc, rmSchedulabilityTest)

        results["light"].append(lightResult)
        results["medlight"].append(medLightResult)
        results["medium"].append(mediumResult)

    return utilizationVals, results

def plotResults(utilVals, results):
    plt.figure()

    LINE_STYLE = ['b:+', 'g-^', 'r-s']

    for (styleId, label) in enumerate(results):
        yvals = results[label]
        plt.plot(utilVals, yvals, LINE_STYLE[styleId], label=label)

        # print("Results for {0}: {1}".format(label, yvals))

    plt.legend(loc="best")

    plt.xlabel("System Utilization")
    plt.ylabel("RM Schedulability")
    plt.title("RM Schedulability for Different Utilization Distributions")

    plt.show()

def testSchedulability():
    random.seed(None) # seed the random library

    # Perform the schedulability tests
    utilVals, results = performTests(1000) # TODO: change to a bigger number, like 1000

    # Plot the results
    plotResults(utilVals, results)

if __name__ == "__main__":
    testSchedulability()