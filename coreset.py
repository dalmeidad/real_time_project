#!/usr/bin/env python

"""
coreset.py - simple coreset and core implementation

Written by: Dawson d'Almeida and Justin Washington
"""

class CoreSetIterator:
    def __init__(self, coreSet):
        self.coreSet = coreSet
        self.index = 0
        self.keys = iter(coreSet.cores)

    def __next__(self):
        key = next(self.keys)
        return self.coreSet.cores[key]

class CoreSet(object):
    def __init__(self, m=2, num_faulty=0, lambda_c=0, lambda_b=0, lambda_r=0):
        self.cores = {}
        self.m = m
        self.num_faulty = num_faulty
        self.lambda_c = lambda_c
        self.lambda_b = lambda_b
        self.lambda_r = lambda_r
        id = 0
        for i in range(m - num_faulty):
            self.cores[i] = Core(id, False, self)
            id += 1
        for i in range(num_faulty):
            self.cores[i] = Core(id, True, self)
            id += 1


    def __contains__(self, elt):
        return elt in self.cores

    def __len__(self):
        return len(self.cores)

    def __iter__(self):
        return CoreSetIterator(self)

    def getCoreById(self, core_id):
        return self.cores[core_id]

    def printCores(self):
        print("\nCore Set:")
        for core in self:
            print(core)

    def printTasks(self):
        print("\nTasks running on cores:")
        for core in self:
            print(core, ": " , core.task)

    def getLowestPriorityCoreGEDF(self, coreList):
        '''
        Returns the core with the lowest priority job executing or a currently not-executing
        core and a boolean representing whether or not the core is executing
        This excludes the cores in the input array
        '''
        lowest_prio_core = self.getCoreById(coreList[0])
        is_executing = lowest_prio_core.is_executing
        # If first core isn't executing, return it
        if not is_executing:
            return lowest_prio_core, False
        for coreId in coreList:
            core = self.getCoreById(coreId)
            if core.is_executing:
                if core.job.deadline > lowest_prio_core.job.deadline:
                    lowest_prio_core = core
            else:
                # Cur core isn't executing, so return it
                return core, False
        # return lowest prio core and True
        return lowest_prio_core, True


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
            # If we set job as None, is_executing should be false
            if job is None:
                self.is_executing = False
            else:
                self.is_executing = True
            return 1
        return 0

    def getIsActive(self):
        return self.is_active

    def deactivateCore(self):
        self.is_active = False

    def activateCore(self):
        self.is_active = True
