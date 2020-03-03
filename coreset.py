#!/usr/bin/env python

"""
coreset.py - simple coreset and core implementation

Written by: Dawson d'Almeida and Justin Washington
"""

class CoreSet(object):
    def __init__(self, m, num_faulty, lambda_c, lambda_b, lambda_r):
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

class Core(object):
    def __init__(self, core_id, is_faulty, core_set):
        self.id = core_id
        self.task = None
        self.is_active = True
        self.is_faulty = is_faulty
        self.coreSet = core_set


    def getTask(self):
        return self.task

    def setTask(self, task):
        if self.is_active:
            self.task = task
            return 1
        return 0

    def getIsActive(self):
        return self.is_active

    def deactivateCore(self):
        self.is_active = False

    def activateCore(self):
        self.is_active = True
