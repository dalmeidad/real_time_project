#!/usr/bin/env python

"""
edf.py - Earliest Deadline First scheduler

EdfPriorityQueue: priority queue that prioritizes by absolute deadline
EdfScheduler: scheduling algorithm that executes EDF (preemptive)
"""

import json
import sys
import math
import random

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

    #we don't use this
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
        if previousJob and previousJob != -1 and (Jobs[0][1].deadline > previousJob.deadline or
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

    def containsJobOrBackup(self, taskId, jobId):
        for curJob in self.jobs:
            if curJob.id == jobId and curJob.task.id == taskId:
                return True
        return False

class FtmGedfScheduler(SchedulerAlgorithm):
    def __init__(self, taskSet, coreSet):
        SchedulerAlgorithm.__init__(self, taskSet, coreSet)
        #has a taskset, coreset, schedule, priorityqueue


    def buildSchedule(self, startTime, endTime):
        self._buildPriorityQueue(EdfPriorityQueue)
        self.time = 0.0
        self.schedule.startTime = self.time
        self.allDeadlinesMet = True
        self.missedJobs = []

        #job that is running on each core
        coresToJobs = {}

        #tracks if the core is in a bursty period. Fault periods are (lB, lG)
        #where intially: lB = [time, time+lBdur) and lG = [time+lBdur, time+lBdur+lGdur)
        coreFaultPeriods = {}
        coresToBursty = {}
        coreLastFaultPeriodStart = {}
        corePermFail = {}
        for core in self.coreSet:
            coresToJobs[core.id] = None
            coreFaultPeriods[core.id] = (0,0)
            coreLastFaultPeriodStart[core.id] = 0
            coresToBursty[core.id] = False
            corePermFail[core.id] = False

        #track if a task.id and job.id have completed for removal of jobs from passive backup and queue
        taskjobComplete = {}
        for job in self.taskSet.jobs: #use job id (as all jobs and their backups have the same job id)
            taskjobComplete[(job.task.id, job.id)] = False

        # Loop until the priority queue is empty, executing jobs preemptively in edf order
        while not self.priorityQueue.isEmpty():
            #set bursty periods 
            #currently each core can have a different lB and lG. Can be easily changed to identical
            for core in self.coreSet:
                if core.is_faulty and not corePermFail[core.id]:
                    if self.time == coreLastFaultPeriodStart[core.id] + sum(coreFaultPeriods[core.id]):
                        coreLastFaultPeriodStart[core.id] = self.time
                        newLB = self.coreSet.getLB()
                        newLG = self.coreSet.getLG()
                        coreFaultPeriods[core.id] = (newLB, newLG)
                    coresToBursty[core.id] = self.time < coreLastFaultPeriodStart[core.id] + coreFaultPeriods[core.id][0] #lB
                    
                    cutoff = random.random()
                    #check permanent fails
                    if cutoff < core.coreSet.lambda_c:
                        corePermFail[core.id] = True
                        core.deactivate()
                    elif (coresToBursty[core.id] and cutoff < core.coreSet.lambda_b) or \
                        (not coresToBursty[core.id] and cutoff < core.coreSet.lambda_r):
                        core.deactivate()
                    else:
                        core.activate()
            # for iterating through cores by Id
            coreListIds = [core.id for core in self.coreSet]
            # build schedule from the queue
            while len(coreListIds) > 0:
                # get the current lowest priority core of the remaining cores
                core, is_executing = self.coreSet.getLowestPriorityCoreGEDF(coreListIds)

                #job currently on the core
                previousJob = core.getJob()
                #placeholder for job we're about to execute 
                job = None
                #if the core is not active, we can just add a fail interval right away
                if not core.is_active:
                    self.schedule.addFailInterval(self.time, self.time+1.0, core.id)
                    job = -1
                else:
                    #check if passive backups needs to be released into priority queue
                    stillNeedToComplete = [job for job in taskjobComplete.keys() if taskjobComplete[job]==False]
                    for ids in stillNeedToComplete:
                        taskId, jobId = ids[0], ids[1]
                        if self.shouldReleasePassive(taskId, jobId):
                            passiveJob = self.taskSet.copyJob(taskId, jobId)
                            self.priorityQueue.addJob(passiveJob)
                            taskjobComplete[(passiveJob.task.id, passiveJob.id)] = False

                    # Make a scheduling decision resulting in an interval
                    interval, job, willFinish = self._makeSchedulingDecision(self.time, previousJob, core)

                    # Execute new job for 1 time step
                    if job and job != -1:
                        if willFinish:
                            if self.time >= job.deadline and not taskjobComplete[(job.task.id, job.id)]:
                                self.allDeadlinesMet = False
                                self.missedJobs.append(job)
                            job.executeToCompletion()
                            taskjobComplete[(job.task.id, job.id)] = True
                        else:
                            job.execute(1)

                    # Add interval to the schedule
                    self.schedule.addInterval(interval)

                # Update the time and job
                coresToJobs[core.id] = job
                core.setJob(job)

                # remove core from current core list to consider
                coreListIds.remove(core.id)

            self.time += 1

        # If there are still previous job, complete them, add intervals
        for core in self.coreSet:
            previousJob = coresToJobs[core.id]
            cur_time = self.time
            if previousJob is not None and previousJob is not -1:
                while previousJob.remainingTime > 0:
                    job_complete = False
                    if previousJob.remainingTime <= 1:
                        previousJob.executeToCompletion()
                        job_complete = True
                    else:
                        previousJob.execute(1)
                    # Add the final idle interval
                    interval = ScheduleInterval()
                    interval.initialize(cur_time, cur_time+1, previousJob, False, core.id, job_complete)
                    self.schedule.addInterval(interval)
                    cur_time += 1
            # Add empty interval at end of each one
            finalInterval = ScheduleInterval()
            finalInterval.initialize(cur_time, cur_time+1, None, False, core.id, False)
            self.schedule.addInterval(finalInterval)

        # Post-process the intervals to set the end time and whether the job completed
        latestDeadline = max([job.deadline for job in self.taskSet.jobs])
        endTime = max(self.time + 1.0, latestDeadline, float(endTime))
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
        if previousJob and previousJob != -1 and previousJob.remainingTime == 0:
            previousJob = None

        # get lowest prio core
        # newJob == previousJob if previousJob has the highest priority
        newJob, didPreemptPrevious = self.priorityQueue.popJob(t, previousJob)
        if newJob and newJob != -1 and newJob.remainingTime <= 1:
            willFinish = True
        # if preempted, add previous job back to queue
        if didPreemptPrevious and previousJob and previousJob != -1:
            self.priorityQueue.addJob(previousJob)

        # update core job
        lowest_core.setJob(newJob)
        # initialize interval
        interval.initialize(t, t+1, newJob, didPreemptPrevious, lowest_core.id, willFinish)

        return interval, newJob, willFinish

    def shouldReleasePassive(self, taskId, jobId):
        '''
        Checks if the original or a backup of a job is still either executing
        or waiting to be executed
        '''
        shouldReleasePassive = True
        for core in self.coreSet:
            curJob = core.getJob()
            if (curJob and curJob != -1) and curJob.task.id == taskId and curJob.id == jobId:
                shouldReleasePassive = False
        if self.priorityQueue.containsJobOrBackup(taskId, jobId):
            shouldReleasePassive = False
        return shouldReleasePassive

    def doesMeetDeadlines(self):
        """
        Returns true if, for every job, either the primary or one of its backups
        meets the deadline
        """
        return self.allDeadlinesMet

    def printMissedJobs(self):
        """
        Print missed jobs. We will integer divide job ids to know which primary job
        it was associated with
        """
        for job in self.missedJobs:
            print("task {0} job {5} backup {6}: (Φ,T,C,D) = ({1}, {2}, {3}, {4})".format(job.task.id, job.task.offset, job.task.period, job.task.wcet,
                                                                       job.deadline, job.id, job.backupId))
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "tasksets/test1.json"

    with open(file_path) as json_data:
        data = json.load(json_data)

    print(data)
    taskSet = TaskSet(data=data, active_backups=1)

    # Construct CoreSet(m, num_faulty, bursty_chance, fault_period_scaler, lambda_c, lambda_b, lambda_r)
    coreSet = CoreSet(m=4, num_faulty=3, lambda_c=0.0)
    coreSet.printCores()

    taskSet.printTasks()
    taskSet.printJobs()

    ftm = FtmGedfScheduler(taskSet, coreSet)
    schedule = ftm.buildSchedule(0, 6)

    schedule.printIntervals(displayIdle=True)

    if ftm.doesMeetDeadlines():
        print("\nAll deadlines are met! :)")
    else:
        print("\nA deadline was missed! :(\n")
        ftm.printMissedJobs()
    
    displayTasks = SchedulingDisplay(width=1200, height=700, fps=33, scheduleData=schedule, display_type='tasks')
    displayTasks.run()

    displayCores = SchedulingDisplay(width=1200, height=700, fps=33, scheduleData=schedule, display_type='cores')
    displayCores.run()
