#!/usr/bin/env python

"""
edf.py - Earliest Deadline First scheduler

EdfPriorityQueue: priority queue that prioritizes by absolute deadline
EdfScheduler: scheduling algorithm that executes EDF (preemptive)
"""

import json
import sys

from taskset import *
from scheduleralgorithm import *
from schedule import ScheduleInterval, Schedule
from display import SchedulingDisplay

class EdfPriorityQueue(PriorityQueue):
    def __init__(self, jobReleaseDict):
        """
        Creates a priority queue of jobs ordered by absolute deadline.
        """
        PriorityQueue.__init__(self, jobReleaseDict)

    def _sortQueue(self):
        # EDF orders by absolute deadline
        self.jobs.sort(key = lambda x: (x.deadline, x.task.id, x.id))

    def _findFirst(self, t):
        """
        Returns the index of the highest-priority job released at or before t,
        or -1 if the queue is empty or if all remaining jobs are released after t.
        """
        if self.isEmpty():
            return -1

        currentJobs = [(i, job) for (i,job) in enumerate(self.jobs) if job.releaseTime <= t]
        if len(currentJobs) == 0:
            return -1

        currentJobs.sort(key = lambda x: (x[1].deadline, x[1].task.id, x[1].id))
        return currentJobs[0][0] # get the index from the tuple in the 0th position

    def popNextJob(self, t):
        """
        Removes and returns the highest-priority job of those released at or after t,
        or None if no jobs are released at or after t.
        """
        laterJobs = [(i, job) for (i,job) in enumerate(self.jobs) if job.releaseTime >= t]

        if len(laterJobs) == 0:
            return t

        laterJobs.sort(key = lambda x: (x[1].releaseTime, x[1].deadline, x[1].task.id))
        return self.jobs.pop(laterJobs[0][0]) # get the index from the tuple in the 0th position

    def popPreemptingJob(self, t, job):
        """
        Removes and returns the job that will preempt job 'job' after time 't', or None
        if no such preemption will occur (i.e., if no higher-priority jobs
        are released before job 'job' will finish executing).

        t: the time after which a preemption may occur
        job: the job that is executing at time 't', and which may be preempted
        """
        if job is None:
            return None

        hpJobs = [(i, j) for (i,j) in enumerate(self.jobs) if \
                  ((j.deadline < job.deadline or (j.deadline == job.deadline and j.task.id < job.task.id)) and \
                    j.releaseTime > t and j.releaseTime < t + job.remainingTime)]

        if len(hpJobs) == 0:
            return None

        hpJobs.sort(key = lambda x: (x[1].releaseTime, x[1].deadline, x[1].task.id))
        return self.jobs.pop(hpJobs[0][0]) # get the index from the tuple in the 0th position

class EdfScheduler(SchedulerAlgorithm):
    def __init__(self, taskSet):
        SchedulerAlgorithm.__init__(self, taskSet)
        SchedulerAlgorithm.__init__(self, taskSet)

    def buildSchedule(self, startTime, endTime):
        self._buildPriorityQueue(EdfPriorityQueue)

        time = 0.0
        self.schedule.startTime = time

        previousJob = None
        didPreemptPrevious = False

        # Loop until the priority queue is empty, executing jobs preemptively in edf order
        while not self.priorityQueue.isEmpty():
            # Make a scheduling decision resulting in an interval
            interval, newJob = self._makeSchedulingDecision(time, previousJob)

            nextTime = interval.startTime
            didPreemptPrevious = interval.didPreemptPrevious

            # If previous interval wasn't idle, execute job for a single time unit
            if previousJob is not None:
                if nextTime - time <= previousJob.remainingTime:
                    previousJob.execute(nextTime - time)
                else:
                    previousJob.executeToCompletion()

            # Add interval to the schedule
            self.schedule.addInterval(interval)

            # Update the time and job
            time = nextTime
            previousJob = newJob

        # If there is still a previous job, complete it and update the time
        if previousJob is not None:
            time += previousJob.remainingTime
            previousJob.executeToCompletion()

        # Add the final idle interval
        finalInterval = ScheduleInterval()
        finalInterval.intialize(time, None, False)
        self.schedule.addInterval(finalInterval)

        # Post-process the intervals to set the end time and whether the job completed
        latestDeadline = max([job.deadline for job in self.taskSet.jobs])
        endTime = max(time + 1.0, latestDeadline, float(endTime))
        self.schedule.postProcessIntervals(endTime)

        return self.schedule

    def _makeSchedulingDecision(self, t, previousJob):
        """
        Makes a scheduling decision after time t.

        t: the beginning of the previous time interval, if one exists (or 0 otherwise)
        previousJob: the job that was previously executing, and will either complete or be preempted

        returns: (ScheduleInterval instance, Job instance of new job to execute)
        """

        interval = ScheduleInterval()
        didPreemptPrevious = False
        nextTime = t

        if previousJob is None:
            # Get the next job after time t
            newJob = self.priorityQueue.popNextJob(nextTime)
            nextTime = newJob.releaseTime
        else:
            # Get the highest priority job at or before nextTime
            # nextTime should be either at the end of previous job or the start of a job that preempts it
            newJob = self.priorityQueue.popPreemptingJob(nextTime, previousJob)
            if newJob is None:
                nextTime += previousJob.remainingTime
                newJob = self.priorityQueue.popFirst(nextTime)
            else:
                self.priorityQueue.addJob(previousJob)
                didPreemptPrevious = True
                nextTime = newJob.releaseTime

        interval.intialize(nextTime, newJob, didPreemptPrevious)

        return interval, newJob

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "tasksets/test1.json"

    with open(file_path) as json_data:
        data = json.load(json_data)

    taskSet = TaskSet(data)

    taskSet.printTasks()
    taskSet.printJobs()

    edf = EdfScheduler(taskSet)
    schedule = edf.buildSchedule(0, 6)

    schedule.printIntervals(displayIdle=True)

    print("\n// Validating the schedule:")
    schedule.checkWcets()
    schedule.checkFeasibility()

    display = SchedulingDisplay(width=800, height=480, fps=33, scheduleData=schedule)
    display.run()
