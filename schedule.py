#!/usr/bin/env python

"""
schedule.py - parser/serializer for schedule to/from JSON file

Written by: Tanya Amert
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

class Schedule(object):
    def __init__(self, data, taskSet):
        self.taskSet = taskSet
        self.intervals = []

        if data is not None:
            # If the schedule has been provided in JSON, parse it
            self.parseJson(data)

    def parseJson(self, data):
        if ScheduleJsonKeys.KEY_SCHEDULE not in data:
            print("Error: Missing schedule info")
            return

        scheduleData = data[ScheduleJsonKeys.KEY_SCHEDULE]
        self.startTime = float(scheduleData[ScheduleJsonKeys.KEY_SCHEDULE_START])

        self.parseDataToIntervals(scheduleData)

    def parseDataToIntervals(self, scheduleData):
        intervals = []

        for intervalData in scheduleData[ScheduleJsonKeys.KEY_INTERVALS]:
            interval = ScheduleInterval(intervalData)
            intervals.append(interval)

        self.intervals = intervals

        endTime = float(scheduleData[ScheduleJsonKeys.KEY_SCHEDULE_END])
        self.postProcessIntervals(endTime)

    def postProcessIntervals(self, endTime):
        self.endTime = endTime

        # Post-process the intervals, setting the end time and whether
        # the job was completed based on the following interval
        for (i, interval) in enumerate(self.intervals):
            if i < len(self.intervals) - 1:
                nextInterval = self.intervals[i+1]
                interval.updateIntervalEnd(nextInterval.startTime, not nextInterval.didPreemptPrevious)
            else:
                interval.updateIntervalEnd(self.endTime, False)

    def addInterval(self, interval):
        self.intervals.append(interval)

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
        else:
            # Default values, needs to be updated
            self.startTime = -1.0
            self.taskId = -1
            self.jobId = -1
            self.didPreemptPrevious = False

    def updateIntervalEnd(self, endTime, didJobComplete):
        self.endTime = endTime
        self.jobCompleted = didJobComplete and not self.taskId == 0 # "idle" jobs don't complete

    def intialize(self, startTime, job, didPreemptPrevious):
        self.startTime = startTime

        if job is not None:
            self.taskId = job.task.id
            self.jobId = job.id
        else:
            self.taskId = 0
            self.jobId = -1

        self.didPreemptPrevious = didPreemptPrevious

    def isIdle(self):
        return self.taskId == 0

    def __str__(self):
        if not self.isIdle():
            return "interval [{0},{1}): task {2}, job {3} (completed: {4}, preempted previous: {5})".format(self.startTime, self.endTime, self.taskId, self.jobId, self.jobCompleted, self.didPreemptPrevious)
        else:
            return "interval [{0},{1}): IDLE (completed: {2}, preempted previous: {3})".format(self.startTime, self.endTime, self.jobCompleted, self.didPreemptPrevious)

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