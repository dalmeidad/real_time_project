#!/usr/bin/env python

"""
schedule.py - parser/serializer for schedule to/from JSON file
"""

import json
import sys

from taskset import TaskSet

class ScheduleJsonKeys(object):
    # Schedule
    KEY_SCHEDULE = "scheduleOutput"
    KEY_SCHEDULE_START = "startTime"
    KEY_SCHEDULE_END = "endTime"

    # Time intervals
    KEY_INTERVALS = "intervals"
    KEY_INTERVAL_START = "timeInstant"
    KEY_INTERVAL_TASKID = "taskId"
    KEY_INTERVAL_JOBID = "jobId"
    KEY_INTERVAL_DIDPREEMPT = "didPreempt"
    KEY_INTERVAL_COREID = "coreId"

class Schedule(object):
    def __init__(self, data, taskSet, coreSet):
        self.taskSet = taskSet
        self.coreSet = coreSet
        self.intervals = []

        if data is not None: #When SchedulerAlgorithm is initialized, data is always NONE
            # If the schedule has been provided in JSON, parse it
            self.parseJson(data)

    #we don't use this
    def parseJson(self, data):
        if ScheduleJsonKeys.KEY_SCHEDULE not in data:
            print("Error: Missing schedule info")
            return

        scheduleData = data[ScheduleJsonKeys.KEY_SCHEDULE]
        self.startTime = float(scheduleData[ScheduleJsonKeys.KEY_SCHEDULE_START])

        self.parseDataToIntervals(scheduleData)

    #we don't use this
    def parseDataToIntervals(self, scheduleData):
        intervals = []

        for intervalData in scheduleData[ScheduleJsonKeys.KEY_INTERVALS]:
            interval = ScheduleInterval(intervalData)
            intervals.append(interval)

        self.intervals = intervals

        endTime = float(scheduleData[ScheduleJsonKeys.KEY_SCHEDULE_END])
        self.postProcessIntervals(endTime)

    #this is called at the very end of each SchedulerAlgorithm's buildSchedule fn
    def postProcessIntervals(self, endTime):
        self.endTime = endTime

        self.intervals.sort(key = lambda x: (x.coreId, x.startTime))
        # Post-process the intervals, setting the end time and whether
        # the job was completed based on the following interval
        for (i, interval) in enumerate(self.intervals):
            #first, find contiguous intervals for all intervals except the last one in the sorted list
            if i != len(self.intervals)-1:
                s = self.intervals[i]
                oneMoreThanLastIndex = i+1
                t = self.intervals[oneMoreThanLastIndex]
                #find last index + 1
                while s.taskId is t.taskId and s.jobId is t.jobId and s.coreId is t.coreId and s.backupId is s.backupId:
                    oneMoreThanLastIndex = oneMoreThanLastIndex+1
                    if oneMoreThanLastIndex < len(self.intervals):
                        t = self.intervals[oneMoreThanLastIndex]
                    else:
                        break
                #update actual start interval
                lastIndex = oneMoreThanLastIndex-1
                if i < lastIndex:
                    self.intervals[i].endTime = self.intervals[lastIndex].endTime
                    self.intervals[i].didPreemptPrevious = self.intervals[lastIndex].didPreemptPrevious
                    self.intervals[i].jobCompleted = self.intervals[lastIndex].jobCompleted
                    #remove the intervals we just combined into the actual start interval
                    del self.intervals[i+1:oneMoreThanLastIndex] #exclusive del [)

            if i < len(self.intervals) - 1:
                nextInterval = self.intervals[i+1]
                interval.updateIntervalEnd(nextInterval.startTime, interval.jobCompleted)
            else:
                interval.updateIntervalEnd(self.endTime, False)

    def addInterval(self, interval):
        self.intervals.append(interval)

    def addFailInterval(self, startTime, endTime, coreId):
        failInterval = ScheduleInterval()
        failInterval.initialize(startTime, endTime, -1, False, coreId, False)
        self.intervals.append(failInterval)
    

    def printIntervals(self, displayIdle=True):
        print("\nScheduling intervals:")
        for interval in self.intervals:
            if not interval.isIdle() or displayIdle:
                print(interval)

    def areWcetsExceeded(self):
        """
        Returns a boolean indicating whether all jobs execute for
        at most their WCET value.
        """
        jobDurations = {}
        for interval in self.intervals:
            if interval.isIdle():
                continue

            task = self.taskSet.getTaskById(interval.taskId)
            job = task.getJobById(interval.jobId)

            key = (task.id, job.id)
            duration = interval.endTime - interval.startTime
            jobDurations[key] = jobDurations.get(key, 0) + duration

            if jobDurations[key] > task.wcet:
                return True

        return False

    def checkWcets(self):
        areWcetsExceeded = self.areWcetsExceeded()
        if not areWcetsExceeded:
            print("No WCETs are exceeded")
        else:
            print("A job exceeds its WCET :(")

    def doesMeetDeadlines(self):
        """
        Returns a boolean indicating whether all deadlines are met.
        """
        for interval in self.intervals:
            if interval.jobCompleted:
                job = self.taskSet.getTaskById(interval.taskId).getJobById(interval.jobId)
                deadline = job.deadline
                finishTime = interval.endTime
                if finishTime > deadline:
                    print("Task {0} Job {1} - r: {2}, d: {3}, f:{4}".format(job.task.id, job.id, job.releaseTime, deadline, finishTime))
                    return False
        return True

    def checkFeasibility(self):
        doesMeetDeadlines = self.doesMeetDeadlines()
        if doesMeetDeadlines:
            print("This schedule is feasible!")
        else:
            print("This schedule is not feasible :(")

class ScheduleInterval(object):
    def __init__(self, intervalDict=None):
        if intervalDict is not None:
            # Parse the JSON dictionary
            self.startTime = float(intervalDict[ScheduleJsonKeys.KEY_INTERVAL_START])
            self.taskId = int(intervalDict[ScheduleJsonKeys.KEY_INTERVAL_TASKID])
            self.jobId = int(intervalDict[ScheduleJsonKeys.KEY_INTERVAL_JOBID])
            self.didPreemptPrevious = bool(intervalDict[ScheduleJsonKeys.KEY_INTERVAL_DIDPREEMPT])
            self.coreId = int(intervalDict[ScheduleJsonKeys.KEY_INTERVAL_COREID])
        else:
            # Default values, needs to be updated
            self.startTime = -1.0
            self.taskId = -1
            self.jobId = -1
            self.didPreemptPrevious = False
            self.coreId = -1
            self.jobCompleted = False
            self.backupId = -1

    def updateIntervalEnd(self, endTime, didJobComplete):
        self.jobCompleted = didJobComplete and not self.taskId == 0 # "idle" jobs don't complete

    def initialize(self, startTime, endTime, job, didPreemptPrevious, coreId, jobCompleted):
        self.startTime = startTime

        if job is -1: #handles Fail periods
            self.taskId = -1
        elif job is not None:
            self.taskId = job.task.id
            self.jobId = job.id
            self.backupId = job.backupId
        else:
            self.taskId = 0
            self.jobId = -1

        self.didPreemptPrevious = didPreemptPrevious
        self.coreId = coreId
        self.endTime = endTime
        self.jobCompleted = jobCompleted

    def isIdle(self):
        return self.taskId == 0
    
    def isFail(self):
        return self.taskId == -1

    def __str__(self):
        if self.isIdle():
            return "interval [{0},{1}): core {4} is IDLE (completed: {2}, preempted previous: {3})".format(self.startTime, self.endTime, self.jobCompleted, self.didPreemptPrevious, self.coreId)
        elif self.isFail():
            return "interval [{0},{1}): core {4} is INACTIVE(completed: {2}, preempted previous: {3})".format(self.startTime, self.endTime, self.jobCompleted, self.didPreemptPrevious, self.coreId)
        else:
            return "interval [{0},{1}): core {6} is executing task {2}, job {3}, backupId {7} (completed: {4}, preempted previous: {5})".format(self.startTime, self.endTime, self.taskId, self.jobId, self.jobCompleted, self.didPreemptPrevious, self.coreId, self.backupId)

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

    schedule = Schedule(data, taskSet)

    schedule.printIntervals(displayIdle=True)

    print("\n// Validating the schedule:")
    schedule.checkWcets()
    schedule.checkFeasibility()
