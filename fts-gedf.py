#!/usr/bin/env python

"""
edf.py - Earliest Deadline First scheduler

EdfPriorityQueue: priority queue that prioritizes by absolute deadline
EdfScheduler: scheduling algorithm that executes EDF (preemptive)
"""

import json
import sys
import math

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

    def popJob(self, t, previousJob):
        """
        Remove and returns the highest-priority job of those release at or before t,
        or None if no jobs are released at or after t.
        """
        Jobs = [(i, job) for (i, job) in enumerate(self.jobs) if job.releaseTime <= t]
        if len(Jobs) == 0:
            return previousJob, False

        Jobs.sort(key=lambda x: (x[1].deadline, x[1].task.id))
        if previousJob and (Jobs[0][1].deadline > previousJob.deadline or
                            (Jobs[0][1].deadline == previousJob.deadline and Jobs[0][1].task.id > previousJob.task.id)):
            return previousJob, False

        # else add previous job and pop new one
        if previousJob:
            return self.jobs.pop(Jobs[0][0]), True  # get the index from the tuple in the 0th position
        return self.jobs.pop(Jobs[0][0]), False

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

        print()

        time = 0.0
        self.schedule.startTime = time

        # Previous jobs -- previous job on each core indexed by core id
        coresToJobs = {}
        jobsToCore = {}

        for core in self.coreSet:
            coresToJobs[core.id] = None

        # Loop until the priority queue is empty, executing jobs preemptively in edf order
        while not self.priorityQueue.isEmpty():

            # iterate through coreList
            coreList = list(self.coreSet.cores.keys())
            while len(coreList) > 0:
                # get the current lowest priority core of the remaining cores
                core, is_executing = self.coreSet.getLowestPriorityCoreGEDF(coreList)
                coreId = core.id

                previousJob = core.getJob()
                # Make a scheduling decision resulting in an interval
                interval, job, willFinish = self._makeSchedulingDecision(time, previousJob, core)

                # Execute new job for 1 time step
                if job:
                    if willFinish:
                        job.executeToCompletion()
                    else:
                        job.execute(1)

                # Add interval to the schedule
                self.schedule.addInterval(interval)

                # Update the time and job
                coresToJobs[coreId] = job
                core.setJob(job)
                if job:
                    jobsToCore[job.id] = coreId

                # remove core from current core list to consider
                coreList.remove(coreId)

            time += 1

        # If there are still previous job, complete them, add intervals
        for core in self.coreSet:
            previousJob = coresToJobs[core.id]
            cur_time = time
            while previousJob.remainingTime > 0:
                if previousJob is not None:
                    job_complete = False
                    print(cur_time, previousJob, previousJob.remainingTime)
                    if previousJob.remainingTime <= 1:
                        previousJob.executeToCompletion()
                        job_complete = True
                    else:
                        previousJob.execute(1)
                    # Add the final idle interval
                    interval = ScheduleInterval()
                    interval.intialize(cur_time, cur_time+1, previousJob, False, core.id, job_complete)
                    self.schedule.addInterval(interval)
                    cur_time += 1
            # Add empty interval at end of each one
            finalInterval = ScheduleInterval()
            finalInterval.intialize(cur_time, cur_time+1, None, False, core.id, job_complete)
            self.schedule.addInterval(finalInterval)


        # Post-process the intervals to set the end time and whether the job completed
        latestDeadline = max([job.deadline for job in self.taskSet.jobs])
        endTime = max(time + 1.0, latestDeadline, float(endTime))
        self.schedule.intervals.sort(key = lambda x: (x.coreId, x.startTime))
        self.schedule.printIntervals(displayIdle = True)
        self.schedule.postProcessIntervals(endTime)
        
        return self.schedule

    def _makeSchedulingDecision(self, t, previousJob, lowest_core):
        """
        Makes a scheduling decision after time t.

        t: the beginning of the previous time interval, if one exists (or 0 otherwise)
        previousJob: the job that was previously executing, and will either complete or be preempted

        returns: (ScheduleInterval instance, Job instance of new job to execute)
        """

        interval = ScheduleInterval()
        willFinish = False
        if previousJob and previousJob.remainingTime == 0:
            previousJob = None

        # get lowest prio core
        # newJob == previousJob if previousJob has the highest priority
        newJob, didPreemptPrevious = self.priorityQueue.popJob(t, previousJob)
        if newJob and newJob.remainingTime <= 1:
            willFinish = True
        # if preempted, add previous job back to queue
        if didPreemptPrevious:
            self.priorityQueue.addJob(previousJob)


        # update core job
        lowest_core.setJob(newJob)
        # initialize interval
        interval.intialize(t, t+1, newJob, didPreemptPrevious, lowest_core.id, willFinish)

        return interval, newJob, willFinish

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
