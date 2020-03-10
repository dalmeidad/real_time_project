import pygame
from taskset import TaskSetJsonKeys, Task, TaskSet
from coreset import CoreSet
import ftmgedf as f

import matplotlib.pyplot as plt
import random
import json

def plotResults(vals, results):
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

if __name__=='__main__':
    file_path1 = "tasksets/test1.json"
    file_path2 = "tasksets/test2.json"
    file_path3 = "tasksets/test3.json"

    # test on different tasksets
    with open(file_path1) as json_data:
        data1 = json.load(json_data)
    with open(file_path2) as json_data:
        data2 = json.load(json_data)
    with open(file_path3) as json_data:
        data3 = json.load(json_data)

    # test changing number of backups
    for i in range(1,2):
        taskSet1 = TaskSet(data=data1, active_backups=i)
        taskSet2 = TaskSet(data=data2, active_backups=i)
        taskSet3 = TaskSet(data=data3, active_backups=i)

    # test changing number of cores
    for i in range(4,5):
        # Construct CoreSet(m, num_faulty, bursty_chance, fault_period_scaler, lambda_c, lambda_b, lambda_r)
        coreSet = CoreSet(m=i, num_faulty=3, lambda_c=0.0)

    # test changing number of faulty cores
    for i in range(3,4):
        coreSet = CoreSet(m=4, num_faulty=i, lambda_c=0.0)

    # test different bursty chance
    for i in range(0):
        coreSet = CoreSet(m=i, num_faulty=3, lambda_c=0.0, bursty_chance=i)

    numTests = 1000
    differentTests = ['2 cores, 3 cores, 4 cores']
    results = {}
    for i in range(len(differentTests)):
        total = 0
        for j in range(numTests):
            ftm = f.FtmGedfScheduler(taskSet1, coreSet)
            schedule = ftm.buildSchedule(0, 6)

            if ftm.doesMeetDeadlines():
                total += 1

        results[differentTests[i]]




    plotResults(vals=[2,3,4], results=results)
