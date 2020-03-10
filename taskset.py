#!/usr/bin/env python

"""
taskset.py - parser for task set from JSON file
"""

import json
import sys

class TaskSetJsonKeys(object):
    # Task set
    KEY_TASKSET = "taskset"

    # Task
    KEY_TASK_ID = "taskId"
    KEY_TASK_PERIOD = "period"
    KEY_TASK_WCET = "wcet"
    KEY_TASK_DEADLINE = "deadline"
    KEY_TASK_OFFSET = "offset"

    # Schedule
    KEY_SCHEDULE_START = "startTime"
    KEY_SCHEDULE_END = "endTime"

    # Release times
    KEY_RELEASETIMES = "releaseTimes"
    KEY_RELEASETIMES_JOBRELEASE = "timeInstant"
    KEY_RELEASETIMES_TASKID = "taskId"

class TaskSetIterator:
    def __init__(self, taskSet):
        self.taskSet = taskSet
        self.index = 0
        self.keys = iter(taskSet.tasks)

    def __next__(self):
        key = next(self.keys)
        return self.taskSet.tasks[key]

class TaskSet(object):
    def __init__(self, data, active_backups=0):
        self.parseDataToTasks(data)
        self.buildJobReleases(data, active_backups)
        print(self.jobs)
        self.num_active_backups = active_backups
        self.passive_backups = self.jobs

    def parseDataToTasks(self, data):
        taskSet = {}

        for taskData in data[TaskSetJsonKeys.KEY_TASKSET]:
            task = Task(taskData)

            if task.id in taskSet:
                print("Error: duplicate task ID: {0}".format(task.id))
                return

            if task.period < 0 and task.relativeDeadline < 0:
                print("Error: aperiodic task must have positive relative deadline")
                return

            taskSet[task.id] = task

        self.tasks = taskSet

    def buildJobReleases(self, data, active_backups):
        jobs = []

        if TaskSetJsonKeys.KEY_RELEASETIMES in data:  # necessary for sporadic releases
            for jobRelease in data[TaskSetJsonKeys.KEY_RELEASETIMES]:
                # add extra jobs to job list for backups
                for i in range(active_backups+1):
                    releaseTime = float(jobRelease[TaskSetJsonKeys.KEY_RELEASETIMES_JOBRELEASE])
                    taskId = int(jobRelease[TaskSetJsonKeys.KEY_RELEASETIMES_TASKID])

                    job = self.getTaskById(taskId).spawnJob(releaseTime)
                    jobs.append(job)
        else:
            scheduleStartTime = float(data[TaskSetJsonKeys.KEY_SCHEDULE_START])
            scheduleEndTime = float(data[TaskSetJsonKeys.KEY_SCHEDULE_END])
            for task in self:
                t = max(task.offset, scheduleStartTime)
                while t < scheduleEndTime:
                    # add extra jobs to job list for backups
                    for i in range(active_backups+1):
                        job = task.spawnJob(t, active_backups)
                        if job is not None:
                            jobs.append(job)

                    if task.period >= 0:
                        t += task.period # periodic
                    else:
                        t = scheduleEndTime # aperiodic

        self.jobs = jobs

    def __contains__(self, elt):
        return elt in self.tasks

    def __iter__(self):
        return TaskSetIterator(self)

    def __len__(self):
        return len(self.tasks)

    def getTaskById(self, taskId):
        return self.tasks[taskId]

    def printTasks(self):
        print("\nTask Set:")
        for task in self:
            print(task)

    def printJobs(self):
        print("\nJobs: (each has {0} active backups)".format(self.num_active_backups))
        for task in self:
            for job in task.getJobs():
                print(job)

class Task(object):
    def __init__(self, taskDict):
        self.id = int(taskDict[TaskSetJsonKeys.KEY_TASK_ID])
        self.period = float(taskDict[TaskSetJsonKeys.KEY_TASK_PERIOD])
        self.wcet = float(taskDict[TaskSetJsonKeys.KEY_TASK_WCET])
        self.relativeDeadline = float(taskDict.get(TaskSetJsonKeys.KEY_TASK_DEADLINE, taskDict[TaskSetJsonKeys.KEY_TASK_PERIOD]))
        self.offset = float(taskDict.get(TaskSetJsonKeys.KEY_TASK_OFFSET, 0.0))

        self.lastJobId = 0
        self.lastReleasedTime = 0.0

        self.jobs = []

    def spawnJob(self, releaseTime, num_backups):
        if self.lastReleasedTime > 0 and releaseTime < self.lastReleasedTime:
            print("INVALID: release time of job is not monotonic")
            return None

        if self.lastReleasedTime > 0 and releaseTime < self.lastReleasedTime + self.period and num_backups == 0:
            print("INVALID: release times are not separated by period")
            return None

        self.lastJobId += 1
        self.lastReleasedTime = releaseTime

        job = Job(self, self.lastJobId, releaseTime)

        self.jobs.append(job)
        return job

    def getJobs(self):
        return self.jobs

    def getJobById(self, jobId):
        if jobId > self.lastJobId:
            return None

        job = self.jobs[jobId-1]
        if job.id == jobId:
            return job

        for job in self.jobs:
            if job.id == jobId:
                return job

        return None

    def __str__(self):
        return "task {0}: (Φ,T,C,D) = ({1}, {2}, {3}, {4})".format(self.id, self.offset, self.period, self.wcet, self.relativeDeadline)

class Job(object):
    def __init__(self, task, jobId, releaseTime):
        self.task = task
        self.id = jobId
        self.releaseTime = releaseTime
        self.deadline = releaseTime + task.relativeDeadline

        self.remainingTime = self.task.wcet

    def execute(self, time):
        executionTime = min(self.remainingTime, time)
        self.remainingTime -= executionTime
        return executionTime

    def executeToCompletion(self):
        return self.execute(self.remainingTime)

    def isCompleted(self):
        return self.remainingTime == 0

    def __str__(self):
        return "[{0}:{1}] released at {2} -> deadline at {3}".format(self.task.id, self.id, self.releaseTime, self.deadline)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "tasksets/hwp1_test1.json"

    with open(file_path) as json_data:
        data = json.load(json_data)

    taskSet = TaskSet(data)

    taskSet.printTasks()
    taskSet.printJobs()
