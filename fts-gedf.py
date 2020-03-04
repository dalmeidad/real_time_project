#!/usr/bin/env python

"""
edf.py - Earliest Deadline First scheduler

EdfPriorityQueue: priority queue that prioritizes by absolute deadline
EdfScheduler: scheduling algorithm that executes EDF (preemptive)
"""

import json
import sys

from taskset import *
from coreset import *
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
    def __init__(self, taskSet, coreSet):
        SchedulerAlgorithm.__init__(self, taskSet, coreSet)


    def buildSchedule(self, startTime, endTime):
        self._buildPriorityQueue(EdfPriorityQueue)

        time = 0.0
        self.schedule.startTime = time

        # Previous jobs -- previous job on each core indexed by core id
        previousJobs = [None for i in range(self.coreSet.m)]
        jobsToCore = {}
        i = 0
        # Loop until the priority queue is empty, executing jobs preemptively in edf order
        while not self.priorityQueue.isEmpty():
            # Make a scheduling decision resulting in an interval
            interval, newJob, coreId, didFinishPrevious = self._makeSchedulingDecision(time, previousJobs)

            nextTime = interval.startTime
            print('time:', time, 'nextTime:', nextTime)

            # If previous interval wasn't idle, execute jobs on each core until next time
            for previousJob in previousJobs:
                if previousJob is not None:
                    if nextTime - time <= previousJob.remainingTime:
                        previousJob.execute(nextTime - time)
                    else:
                        previousJob.executeToCompletion()

                # If a previous job finished, set core activity to not active and pop job core relationship
                if didFinishPrevious:
                    core = self.coreSet.getCoreById(coreId)
                    core.setJob(None)
                    core.is_active = False
                    jobsToCore.pop(previousJob.id, None)

            # Add interval to the schedule
            self.schedule.addInterval(interval)

            # Update the time and job
            time = nextTime
            previousJobs[coreId] = newJob
            if newJob:
                jobsToCore[newJob.id] = coreId
            i += 1

        # If there are still previous job, complete them, add intervals
        for previousJob in previousJobs:
            if previousJob is not None:
                time += previousJob.remainingTime
                previousJob.executeToCompletion()
                # Add the final idle interval
                finalInterval = ScheduleInterval()
                finalInterval.intialize(time, None, False, jobsToCore[previousJob.id])
                self.schedule.addInterval(finalInterval)

        # Post-process the intervals to set the end time and whether the job completed
        latestDeadline = max([job.deadline for job in self.taskSet.jobs])
        endTime = max(time + 1.0, latestDeadline, float(endTime))
        self.schedule.postProcessIntervals(endTime)

        return self.schedule

    def _makeSchedulingDecision(self, t, previousJobs):
        """
        Makes a scheduling decision after time t.

        t: the beginning of the previous time interval, if one exists (or 0 otherwise)
        previousJob: the job that was previously executing, and will either complete or be preempted

        returns: (ScheduleInterval instance, Job instance of new job to execute)
        """

        interval = ScheduleInterval()
        didPreemptPrevious = False
        didFinishPrevious = False
        nextTime = t

        # get lowest prio core
        lowest_core, is_executing = self.coreSet.getLowestPriorityCoreGEDF()

        # Find first inactive core if one exists
        if not is_executing:
            print('not is_executing')
            coreId = lowest_core.id
            newJob = self.priorityQueue.popNextJob(nextTime)
            nextTime = newJob.releaseTime
        else: # Find current lowest priority core to preempt
            print('is_executing')
            coreId = lowest_core.id
            previousJob = lowest_core.job
            newJob = self.priorityQueue.popNextJob(nextTime)
            # If there is no job to preempt at or after nextTime, finish job
            if newJob is None or newJob.deadline >= lowest_core.job.deadline:
                nextTime += previousJob.remainingTime
                didFinishPrevious = True
                # If the job doesn't have a higher prio than the lowest prio, add back to queue
                if newJob.deadline >= lowest_core.job.deadline:
                    self.priorityQueue.addJob(newJob)
                newJob = self.priorityQueue.popFirst(nextTime)
            else:
                self.priorityQueue.addJob(lowest_core.job)
                lowest_core.job = newJob
                nextTime = newJob.releaseTime
                didPreemptPrevious = True

        # update core job
        lowest_core.setJob(newJob)

        # initialize interval
        interval.intialize(nextTime, newJob, didPreemptPrevious, coreId)

        return interval, newJob, coreId, didFinishPrevious

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "tasksets/test1.json"

    with open(file_path) as json_data:
        data = json.load(json_data)

    taskSet = TaskSet(data)

    # Construct CoreSet(m, num_faulty, lambda_c, lambda_b, lambda_r)
    coreSet = CoreSet()

    taskSet.printTasks()
    taskSet.printJobs()

    edf = EdfScheduler(taskSet, coreSet)
    schedule = edf.buildSchedule(0, 6)

    schedule.printIntervals(displayIdle=True)

    print("\n// Validating the schedule:")
    schedule.checkWcets()
    schedule.checkFeasibility()

    display = SchedulingDisplay(width=800, height=480, fps=33, scheduleData=schedule)
    display.run()
