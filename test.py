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
        plt.plot(vals, yvals, LINE_STYLE[styleId], label=label)

        # print("Results for {0}: {1}".format(label, yvals))

    plt.legend(loc="best")

    plt.xlabel("Number of backups")
    plt.ylabel("FTS-GEDF Schedulability")
    plt.title("Number of backups for different task systems")

    plt.show()

if __name__=='__main__':
    file_path1 = "tasksets/test4.json"
    file_path2 = "tasksets/test5.json"
    file_path3 = "tasksets/test7.json"

    # test on different tasksets
    data = []
    with open(file_path1) as json_data:
        data.append(json.load(json_data))
    with open(file_path2) as json_data:
        data.append(json.load(json_data))
    with open(file_path3) as json_data:
        data.append(json.load(json_data))

    different_num_backups = [1,2,3,4,5,6,7,8,9,10]

    # test changing number of backups
    dataSets = {}
    different_data_sets = ['short short short long', 'all short', 'all long']
    for dataSet in different_data_sets:
        dataSets[dataSet] = []


    i = 0
    for dataSet in data:
        taskSets = []
        coreSets = []
        for j in different_num_backups:
            taskSets.append(TaskSet(data=dataSet, active_backups=j))
            coreSets.append(CoreSet(m=4, num_faulty=4, lambda_c=0.0))
            dataSets[different_data_sets[i]].append((taskSets, coreSets))
        i += 1

    numTests = 20
    results = {}
    for dataSet in different_data_sets:
        results[dataSet] = []


    for dataSet in different_data_sets:
        i = 0
        for num_backup in different_num_backups:
            total = 0
            for j in range(numTests):
                taskCore = dataSets[dataSet][i]
                taskSet = taskCore[0]
                coreSet = taskCore[1]

                ftm = f.FtmGedfScheduler(taskSet[0], coreSet[0])
                schedule = ftm.buildSchedule(0, 50)

                if ftm.doesMeetDeadlines():
                    total += 1

            results[dataSet].append(total / numTests)
            i += 1



    print(different_num_backups, results)
    plotResults(vals=different_num_backups, results=results)
