#!/usr/bin/env python

"""
schedulerAlgorithm.py

PriorityQueue: base class for priority queues used to maintain the queue of jobs
SchedulerAlgorithm: base class for scheduling algorithms
"""

from schedule import Schedule
from taskset import TaskSet

class PriorityQueue(object):
    def __init__(self, jobReleaseDict):
        """
        Builds the priority queue of all jobs.
        This will need to be sorted to match the scheduling algorithm.
        """
        self.jobs = []

        releaseTimes = sorted(jobReleaseDict.keys())
        for time in releaseTimes:
            for job in jobReleaseDict[time]:
                self.jobs.append(job)

        self._sortQueue()

    def isEmpty(self):
        """
        Returns a boolean indicating whether the priority queue is empty.
        """
        return len(self.jobs) == 0

    def addJob(self, job):
        """
        Adds a job to the priority queue.
        """
        self.jobs.append(job)
        self._sortQueue()

    def removeJob(self, job):
        if job in self.jobs:
            self.jobs.remove(job)
            return True
        return False

    def getFirst(self, t):
        """
        Returns the job with highest priority at time t, or None
        if no such jobs exist.
        """
        index = self._findFirst(t)
        if index >= 0:
            return self.jobs[index]
        else:
            return None

    def popFirst(self, t):
        """
        Removes and returns the job with the highest priority at time t,
        if one exists.
        """
        index = self._findFirst(t)
        if index >= 0:
            return self.jobs.pop(index)

    def _popJob(self, t):
        raise NotImplementedError

    def _sortQueue(self):
        raise NotImplementedError

    def _findFirst(self, t):
        raise NotImplementedError

    def popNextJob(self, t):
        raise NotImplementedError

    def popPreemptingJob(self, t, job):
        raise NotImplementedError

    def __contains__(self, job):
        for q in self.jobs:
            if q.id is job.id and q.task.id is job.task.id:
                return True
        return False

class SchedulerAlgorithm(object):
    def __init__(self, taskSet, coreSet):
        self.taskSet = taskSet
        self.coreSet = coreSet

        self.schedule = Schedule(None, taskSet, coreSet)
        self.time = 0 #TODO:do we need this?

    def buildSchedule(self):
        raise NotImplementedError()

    def makeSchedulingDecision(self, t):
        raise NotImplementedError()

    def _buildPriorityQueue(self, queueType):
        """
        Builds and returns the priority queue of jobs.

        queueType: the class name of the type of priority queue to create
        """
        jobReleases = {}

        for job in self.taskSet.jobs:
            r = job.releaseTime

            if r not in jobReleases:
                jobReleases[r] = [job]
            else:
                jobReleases[r].append(job)

        self.priorityQueue = queueType(jobReleases)