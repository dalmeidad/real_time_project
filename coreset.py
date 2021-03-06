#!/usr/bin/env python

"""
coreset.py - simple coreset and core implementation

Written by: Dawson d'Almeida and Justin Washington
"""
import numpy as np

class CoreSetIterator:
    def __init__(self, coreSet):
        self.coreSet = coreSet
        self.index = 0
        self.keys = iter(coreSet.cores)

    def __next__(self):
        key = next(self.keys)
        return self.coreSet.cores[key]

class CoreSet(object):
    def __init__(self, m=1, num_faulty=0, bursty_chance=0.3, fault_period_scaler=3,
                 lambda_c=0.02, lambda_b=0.5, lambda_r=0.08):
        self.cores = {}
        self.m = m
        self.num_faulty = num_faulty
        coreId = 0
        for i in range(num_faulty):
            self.cores[coreId] = Core(coreId, True, self)
            coreId += 1
        for i in range(m-num_faulty):
            self.cores[coreId] = Core(coreId, False, self)
            coreId += 1
        self.lambda_c = lambda_c
        self.lambda_b = lambda_b
        self.lambda_r = lambda_r
        self.fault_period_scaler = fault_period_scaler
        #seems backwards, but it isn't. Lower bursty_chance = higher score in geometric
        #distrubution, meaning lGap is longer. 
        self.lGapProb = bursty_chance
        self.lBurstProb = 1-bursty_chance


    def __contains__(self, elt):
        return elt in self.cores

    def __len__(self):
        return len(self.cores)

    def __iter__(self):
        return CoreSetIterator(self)

    def printCores(self):
        print("\nCore Set:")
        for core in self.cores.values():
            print(core)

    def getCoreById(self, core_id):
        return self.cores[core_id]


    def printTasks(self):
        print("\nTasks running on cores:")
        for core in self:
            print(core, ": " , core.task)

    def getLowestPriorityCoreGEDF(self, coreList):
        """
        Returns the core in coreList with the lowest priority job executing 
        or a currently not-executing core and a boolean representing whether 
        or not the core is executing
        """
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

    def getLB(self):
        return np.random.geometric(self.lBurstProb)*self.fault_period_scaler
    
    def getLG(self):
        return np.random.geometric(self.lGapProb)*self.fault_period_scaler

    def __contains__(self, job):
        for core in list(self.cores.values()):
            if core.job is not None and core.job.id is job.id and core.job.task.id is job.task.id:
                return True
        return False


class Core(object):
    def __init__(self, core_id, is_faulty, core_set):
        self.id = core_id           #id
        self.job = None             #job executing on the core
        self.is_faulty = is_faulty  #if the core has the potential to fail
        self.is_active = True       #if the core is failing or not
        self.is_executing = False   #if the core is executing a job (core has to be active)
        self.coreSet = core_set     #the coreset the core belongs to

    def __str__(self):
        if self.is_active and self.is_executing:
            if self.is_faulty:
                return "Faulty core {0} is active and executing Task {1},{2},{3}".\
                    format(self.id, self.job.task.id, self.job.id, self.job.backupId)
            else:
                return "Stable core {0} is active and executing Task {1},{2},{3}".\
                    format(self.id, self.job.task.id, self.job.id, self.job.backupId)
        elif self.is_active:
            if self.is_faulty:
                return "Faulty core {0} is active and not executing".format(self.id)
            else:
                return "Stable core {0} is active and not executing".format(self.id)
        else:
            return "Faulty core {0} is not active".format(self.id)

    def getJob(self):
        return self.job

    def setJob(self, job):
        if job == -1:
            self.is_active = False
            self.is_executing = False
        elif job is None: # If we set job as None, is_executing should be false
            self.is_executing = False
            self.is_active = True
        else:
            self.is_executing = True
            self.is_active = True
        self.job = job

    def deactivate(self):
        if self.is_faulty:
            self.is_active = False
            self.is_executing = False

    def activate(self):
        self.is_active = True


