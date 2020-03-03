#!/usr/bin/env python

"""
display.py - display for CS 330 scheduling library

Written by: Tanya Amert
"""

import json
import math
import pygame
import sys

from taskset import TaskSet
from schedule import Schedule

BUFFER_TOP = 0
BUFFER_BOTTOM = 68

BUFFER_LEFT = 52
BUFFER_RIGHT = 52

USE_BOLD_FONT = True
IS_FOR_PRINT = True

LINE_WIDTH = 2

##################################################################
##  Static display elements                                     ##
##################################################################

class XAxis(object):
    def __init__(self, startTime, endTime, w, h):
        self.build_axis(w, h)

        totalTime = endTime - startTime
        tickTime = self.calculate_tick_time(totalTime)
        tickLabelTime = self.calculate_tick_label_time(totalTime)
        self.build_tick_marks(totalTime, tickTime, w, h)
        self.build_labels(totalTime, tickLabelTime, w, h)

    def build_axis(self, w, h):
        # Draw a thin black horizontal line
        p1x = BUFFER_LEFT
        p2x = w - BUFFER_RIGHT

        py = h - BUFFER_BOTTOM + LINE_WIDTH // 2

        # Store the axis as a tuple of pos tuples, and the line width:
        # (p1, p2, w)
        self.axis = ((p1x, py), (p2x, py), LINE_WIDTH)

    def calculate_tick_time(self, totalTime):
        if totalTime <= 2.0:
            return 0.1
        elif totalTime <= 4.0:
            return 0.2
        elif totalTime <= 7.0:
            return 0.5
        elif totalTime <= 10.0:
            return 1.0
        elif totalTime <= 16.0:
            return 2.0
        else:
            return 5.0

    def calculate_tick_label_time(self, totalTime):
        if totalTime <= 2.0:
            return 0.1
        elif totalTime <= 4.0:
            return 0.2
        elif totalTime <= 7.0:
            return 0.5
        elif totalTime <= 10.0:
            return 1.0
        elif totalTime <= 16.0:
            return 2.0
        else:
            return 5.0

    def build_tick_marks(self, totalTime, tickTime, w, h):
        # Put a tick every tickTime seconds
        plotWidth = w - BUFFER_LEFT - BUFFER_RIGHT
        numTicks = int(math.ceil(totalTime / tickTime))
        self.ticks = []
        for i in range(0, numTicks+1):
            px = BUFFER_LEFT + (i * tickTime / totalTime) * plotWidth

            if px > w - BUFFER_RIGHT:
                continue

            p1y = h - BUFFER_BOTTOM - 0 + LINE_WIDTH
            p2y = h - BUFFER_BOTTOM - 4 + LINE_WIDTH

            # Store the tick as a tuple of pos tuples, and the line width:
            # (p1, p2, w)
            tick = ((px, p1y), (px, p2y), LINE_WIDTH)
            self.ticks.append(tick)

    def build_labels(self, totalTime, tickTime, w, h):
        # Put a label every tick mark
        plotWidth = w - BUFFER_LEFT - BUFFER_RIGHT
        numTicks = int(math.ceil(totalTime / tickTime))
        font = pygame.font.SysFont("mono", int(30 * (h / 720)), bold=USE_BOLD_FONT)
        self.labels = []
        for i in range(0, numTicks + 1):
            px = BUFFER_LEFT + (i * tickTime / totalTime) * plotWidth

            if px > w - BUFFER_RIGHT:
                continue

            py = h - int(BUFFER_BOTTOM * 0.9)

            # Store the text as a tuple of the string, pos tuple, and font:
            # (s, pos, font)
            label = ("{0:.1f}".format(i * tickTime),  (px, py), font)
            self.labels.append(label)

        # Give the axis a label
        px = w / 2
        py = h - (BUFFER_BOTTOM * 0.4)
        label = ("Time (seconds)",  (px, py), font)
        self.labels.append(label)

    def draw(self, surface):
        # Draw the axis line
        p1, p2, lineWidth = self.axis
        pygame.draw.line(surface, SchedulingDisplayColors.TIME_BAR, p1, p2, lineWidth)

        # Draw the tick marks
        for tick in self.ticks:
            p1, p2, lineWidth = tick
            pygame.draw.line(surface, SchedulingDisplayColors.TIME_TICK, p1, p2, lineWidth)

        # Draw the tick labels
        for label in self.labels:
            text, pos, font = label
            fw, fh = font.size(text)
            # px = (pos[0] - fw) // 2 # specify top left
            # py = (pos[1] - fh) // 2
            px = pos[0] - (fw // 2)
            py = pos[1]
            color = SchedulingDisplayColors.TIME_TICK_LABEL

            labelSurface = font.render(text, True, color)
            surface.blit(labelSurface, (px, py))

class YAxis(object):
    def __init__(self, taskSet, startTime, endTime, w, h):
        self.build_grid_lines(len(taskSet), w, h)
        self.build_labels(taskSet, w, h)

    def build_grid_lines(self, numTasks, w, h):
        # Put a horizontal line between each task
        plotHeight = h - BUFFER_TOP  - BUFFER_BOTTOM
        plotBottom = h - BUFFER_BOTTOM
        taskHeight = plotHeight / numTasks
        self.gridlines = []
        for i in range(1, numTasks):
            py = plotBottom - i * taskHeight + LINE_WIDTH

            p1x = BUFFER_LEFT
            p2x = w - BUFFER_RIGHT

            # Store the line as a tuple of pos tuples, and the line width:
            # (p1, p2, w)
            gridline = ((p1x, py), (p2x, py), LINE_WIDTH)
            self.gridlines.append(gridline)

    def build_labels(self, taskSet, w, h):
        numTasks = len(taskSet)
        plotHeight = h - BUFFER_TOP - BUFFER_BOTTOM
        plotBottom = h - BUFFER_BOTTOM
        taskHeight = plotHeight / numTasks
        font = pygame.font.SysFont("mono", int(30 * (h / 720)), bold=USE_BOLD_FONT)
        self.labels = []
        for (i, task) in enumerate(taskSet):
            px = int(BUFFER_LEFT * 0.8)
            py = plotBottom - (numTasks - i - 1) * taskHeight - int(0.5 * taskHeight)

            # Store the text as a tuple of the string, pos tuple, and font:
            # (s, pos, font)
            label = ("τ{0}".format(task.id),  (px, py), font)
            self.labels.append(label)

    def draw(self, surface):
        # Draw the grid lines
        for gridline in self.gridlines:
            p1, p2, lineWidth = gridline
            pygame.draw.line(surface, SchedulingDisplayColors.TIME_BAR, p1, p2, lineWidth)

        # Draw the tasks' labels
        for label in self.labels:
            text, pos, font = label
            fw, fh = font.size(text)
            px = pos[0] - fw
            py = pos[1]
            color = SchedulingDisplayColors.TASK_LABEL

            labelSurface = font.render(text, True, color)
            surface.blit(labelSurface, (px, py))

##################################################################
##  Interval display elements                                   ##
##################################################################

class IntervalRect(object):
    def __init__(self, interval, startTime, endTime, numTasks, w, h, color):
        self.build_rectangle(interval, startTime, endTime, numTasks, w, h, color)

    def build_rectangle(self, interval, startTime, endTime, numTasks, w, h, color):
        plotHeight = h - BUFFER_TOP - BUFFER_BOTTOM
        plotBottom = h - BUFFER_BOTTOM
        taskHeight = plotHeight / numTasks

        intervalBottom = plotBottom - int((numTasks - interval.taskId) * taskHeight)
        intervalHeight = int(taskHeight * 0.4)
        intervalTop = intervalBottom - intervalHeight

        totalTime = endTime - startTime
        p1x = int(float(interval.startTime - startTime) / totalTime * (w-BUFFER_LEFT-BUFFER_RIGHT)) + BUFFER_LEFT
        p1y = intervalBottom - intervalHeight

        rectW = int(float(interval.endTime - startTime) / totalTime * (w-BUFFER_LEFT-BUFFER_RIGHT)) + BUFFER_LEFT - p1x - 1 # open interval on RHS
        rectH = intervalHeight

        # Store the rect as a tuple: (x1, y1, width, height)
        self.rect = (p1x, p1y, rectW, rectH)

        # Draw the outline separately
        self.outlineWidth = LINE_WIDTH

    def draw(self, surface):
        px, py, w, h = self.rect
        fillColor = SchedulingDisplayColors.INTERVAL_FILL

        lineWidth = self.outlineWidth
        lineColor = SchedulingDisplayColors.INTERVAL_BORDER

        pygame.draw.rect(surface, fillColor, self.rect, 0)
        pygame.draw.rect(surface, lineColor, self.rect, lineWidth)

##################################################################
##  Job display elements                                        ##
##################################################################

class ReleaseArrow(object):
    def __init__(self, releaseTime, taskId, numTasks, startTime, endTime, w, h, color):
        self.build_arrow(releaseTime, taskId, numTasks, startTime, endTime, w, h, color)

    def build_arrow(self, releaseTime, taskId, numTasks, startTime, endTime, w, h, color):
        plotHeight = h - BUFFER_TOP - BUFFER_BOTTOM
        plotBottom = h - BUFFER_BOTTOM
        taskHeight = plotHeight / numTasks

        arrowBottom = plotBottom - int((numTasks - taskId) * taskHeight)
        arrowHeight = int(taskHeight * 0.6)
        arrowHeadHeight = int(arrowHeight * 0.2)
        arrowHeadWidth = int(arrowHeight * 0.3)

        totalTime = endTime - startTime
        pmx = int(float(releaseTime - startTime) / totalTime * (w-BUFFER_LEFT-BUFFER_RIGHT)) + BUFFER_LEFT
        pby = arrowBottom

        plx = pmx - arrowHeadWidth // 2
        prx = pmx + arrowHeadWidth // 2

        pty = pby - arrowHeight
        pmy = pty + arrowHeadHeight # upward arrow

        # Store the arrow as a tuple of lines, each of which
        # is a tuple of p1, p2: (vertLine, leftHead, rightHead)
        self.lines = (((pmx, pby), (pmx, pty)), # vertical line
                      ((plx, pmy), (pmx, pty)), # left side of head
                      ((prx, pmy), (pmx, pty))) # right side of head
        self.lineWidth = LINE_WIDTH

    def draw(self, surface):
        for line in self.lines:
            p1, p2 = line
            lineColor = SchedulingDisplayColors.RELEASE_ARROW
            lineWidth = self.lineWidth

            pygame.draw.line(surface, lineColor, p1, p2, lineWidth)

class DeadlineArrow(object):
    def __init__(self, deadlineTime, taskId, numTasks, startTime, endTime, w, h, color):
        self.build_arrow(deadlineTime, taskId, numTasks, startTime, endTime, w, h, color)

    def build_arrow(self, deadlineTime, taskId, numTasks, startTime, endTime, w, h, color):
        plotHeight = h - BUFFER_TOP - BUFFER_BOTTOM
        plotBottom = h - BUFFER_BOTTOM
        taskHeight = plotHeight / numTasks

        arrowBottom = plotBottom - int((numTasks - taskId) * taskHeight)
        arrowHeight = int(taskHeight * 0.6)
        arrowHeadHeight = int(arrowHeight * 0.2)
        arrowHeadWidth = int(arrowHeight * 0.3)

        totalTime = endTime - startTime
        pmx = int(float(deadlineTime - startTime) / totalTime * (w-BUFFER_LEFT-BUFFER_RIGHT)) + BUFFER_LEFT
        pby = arrowBottom

        plx = pmx - arrowHeadWidth // 2
        prx = pmx + arrowHeadWidth // 2

        pty = pby - arrowHeight
        pmy = pby - arrowHeadHeight # downward arrow

        # Store the arrow as a tuple of lines, each of which
        # is a tuple of p1, p2: (vertLine, leftHead, rightHead)
        self.lines = (((pmx, pby), (pmx, pty)), # vertical line
                      ((plx, pmy), (pmx, pby)), # left side of head
                      ((prx, pmy), (pmx, pby))) # right side of head
        self.lineWidth = LINE_WIDTH

    def draw(self, surface):
        for line in self.lines:
            p1, p2 = line
            lineColor = SchedulingDisplayColors.DEADLINE_ARROW
            lineWidth = self.lineWidth

            pygame.draw.line(surface, lineColor, p1, p2, lineWidth)

class CompletionHat(object):
    def __init__(self, completionTime, taskId, numTasks, startTime, endTime, w, h, color):
        self.build_arrow(completionTime, taskId, numTasks, startTime, endTime, w, h, color)

    def build_arrow(self, completionTime, taskId, numTasks, startTime, endTime, w, h, color):
        plotHeight = h - BUFFER_TOP - BUFFER_BOTTOM
        plotBottom = h - BUFFER_BOTTOM
        taskHeight = plotHeight / numTasks

        shaftBottom = plotBottom - int((numTasks - taskId) * taskHeight)
        shaftHeight = int(taskHeight * 0.5)
        hatWidth = int(shaftHeight * 0.3)

        totalTime = endTime - startTime
        pmx = int(float(completionTime - startTime) / totalTime * (w-BUFFER_LEFT-BUFFER_RIGHT)) + BUFFER_LEFT - 1 # open interval on RHS

        pby = shaftBottom
        pty = pby - shaftHeight

        plx = pmx - hatWidth // 2
        prx = pmx + hatWidth // 2

        # Store the hat as a tuple of lines, each of which
        # is a tuple of p1, p2: (shaft, hat)
        self.lines = (((pmx, pby), (pmx, pty)), # vertical line
                      ((plx, pty), (prx, pty))) # horizontal line
        self.lineWidth = LINE_WIDTH

    def draw(self, surface):
        for line in self.lines:
            p1, p2 = line
            lineColor = SchedulingDisplayColors.COMPLETION_HAT
            lineWidth = self.lineWidth

            pygame.draw.line(surface, lineColor, p1, p2, lineWidth)

##################################################################
##  Overall display                                             ##
##################################################################

class SchedulingDisplayColors(object):
    if IS_FOR_PRINT:
        # Better color choices if printing
        BACKGROUND      = (255, 255, 255)  # white
        TASK_LABEL      = ( 40,  40,  40)  # dark gray
        TIME_BAR        = (  0,   0,   0)  # black
        TIME_TICK_LABEL = ( 40,  40,  40)  # dark gray
        TIME_TICK       = (  0,   0,   0)  # black
        RELEASE_ARROW   = ( 20, 100,  40)  # dark green
        DEADLINE_ARROW  = (100,  20,  40)  # dark red
        COMPLETION_HAT  = (  20, 40, 100)  # dark blue
        INTERVAL_BORDER = (  0,   0,   0)  # black
        INTERVAL_FILL   = (128, 128, 128)  # light gray
    else:
        # Fun display for screens
        BACKGROUND      = ( 40,  40,  40)  # dark gray
        TASK_LABEL      = (255,   0, 128)  # magenta
        TIME_BAR        = (255, 128,   0)  # orange
        TIME_TICK_LABEL = (128,   0, 255)  # purple
        TIME_TICK       = (128, 255,   0)  # red-green
        RELEASE_ARROW   = (128, 128, 128)  # light gray
        DEADLINE_ARROW  = (  0, 255, 128)  # blue-green
        COMPLETION_HAT  = (255, 248, 100)  # yellow
        INTERVAL_BORDER = (255, 255, 255)  # white
        INTERVAL_FILL   = (  0, 128, 255)  # blue

class SchedulingDisplay(object):
    def __init__(self, width=1080, height=720, fps=30, scheduleData=None):
        pygame.init()
        pygame.display.set_caption("CS 330 Scheduling Display")

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)

        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill(SchedulingDisplayColors.BACKGROUND)
        self.background = self.background.convert()

        self.clock = pygame.time.Clock()
        self.fps = fps

        self.scheduleData = scheduleData

    def parse_input(self):
        """
        Parse user input from the keyboard.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                    print("Saving schedule as screenshot.png")
                    pygame.image.save(self.screen, "screenshot.png")

    def run(self):
        """
        The main loop: check for user input, then update the display.
        """
        self.running = True
        while self.running:
            self.parse_input()

            self.clock.tick(self.fps)

            if self.scheduleData is not None:
                self.draw_schedule()

            self.draw_axes()

            pygame.display.flip()
            self.screen.blit(self.background, (0, 0))

        pygame.quit()

    def draw_schedule(self):
        numTasks = len(self.scheduleData.taskSet)
        scheduleStartTime = self.scheduleData.startTime
        scheduleEndTime = self.scheduleData.endTime

        for (i, interval) in enumerate(reversed(self.scheduleData.intervals)):
            if interval.taskId == 0:
                continue

            intervalRect = IntervalRect(interval, scheduleStartTime, scheduleEndTime, numTasks, self.width, self.height, None)
            intervalRect.draw(self.background)

        for task in self.scheduleData.taskSet:
            for job in task.jobs:
                releaseTime = job.releaseTime
                releaseArrow = ReleaseArrow(releaseTime, task.id, numTasks, scheduleStartTime, scheduleEndTime, self.width, self.height, None)
                releaseArrow.draw(self.background)

                deadlineTime = job.deadline
                deadlineArrow = DeadlineArrow(deadlineTime, task.id, numTasks, scheduleStartTime, scheduleEndTime, self.width, self.height, None)
                deadlineArrow.draw(self.background)

        for interval in self.scheduleData.intervals:
            if interval.jobCompleted:
                completionHat = CompletionHat(interval.endTime, interval.taskId, numTasks, scheduleStartTime, scheduleEndTime, self.width, self.height, None)
                completionHat.draw(self.background)

    def draw_axes(self):
        if self.scheduleData is not None:
            xaxis = XAxis(self.scheduleData.startTime, self.scheduleData.endTime, self.width, self.height)
            xaxis.draw(self.background)

            yaxis = YAxis(self.scheduleData.taskSet, self.scheduleData.startTime, self.scheduleData.endTime, self.width, self.height)
            yaxis.draw(self.background)

if __name__ == '__main__':
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

    schedule.printIntervals()

    display = SchedulingDisplay(width=600, height=480, fps=33, scheduleData=schedule)

    display.run()