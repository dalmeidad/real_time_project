#!/usr/bin/env python

"""
coreset.py - simple coreset and core implementation

Written by: Dawson d'Almeida and Justin Washington
"""

class CoreSet(object):
    def __init__(self, m=1, num_faulty=0, lambda_c=0, lambda_b=0, lambda_r=0):
        self.cores = []
        self.m = m
        self.num_faulty = num_faulty
        self.lambda_c = lambda_c
        self.lambda_b = lambda_b
        self.lambda_r = lambda_r
        id = 0
        for i in range(m - num_faulty):
            self.cores.append(Core(id, False, self))
            id += 1
        for i in range(num_faulty):
            self.cores.append(Core(id, True, self))
            id += 1


    def __contains__(self, elt):
        return elt in self.cores

    def __len__(self):
        return len(self.cores)

    def getCoreById(self, core_id):
        return self.core[core_id]

    def printCores(self):
        print("\nCore Set:")
        for core in self:
            print(core)

    def printTasks(self):
        print("\nTasks running on cores:")
        for core in self:
            print(core, ": " , core.task)

    def getLowestPriorityCore(self):
        lowest_prio_core = self.cores[0]
        latest_deadline = lowest_prio_core.job.deadline
        for core in self.cores:
            if core.job.deadline > lowest_prio_core.job.deadline:
                lowest_prio_core = core
                latest_deadline = core.job.deadline
        return lowest_prio_core


class Core(object):
    def __init__(self, core_id, is_faulty, core_set):
        self.id = core_id
        self.job = None
        self.is_active = True
        self.is_executing = False
        self.is_faulty = is_faulty
        self.coreSet = core_set


    def getJob(self):
        return self.job

    def setJob(self, job):
        if self.is_active:
            self.job = job
            return 1
        return 0

    def getIsActive(self):
        return self.is_active

    def deactivateCore(self):
        self.is_active = False

    def activateCore(self):
        self.is_active = True
