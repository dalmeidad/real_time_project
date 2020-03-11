Justin Washington and Dawson d'Almeida

Testing: Real-time scheduling algorithm for safety-critical systems on faulty multicore environments
Link: https://link.springer.com/article/10.1007%2Fs11241-016-9258-z#Sec4

To Test:
python ftmgedf.py [taskset.json]

Task window:
This shows how tasks completed. Completion hats can be for either primary jobs or backups. A deadline is definitely missed if a completion
hat closer to a release than the WCET, but it can be hard to tell otherwise.

Core window:
This shows the progression of execution on all cores. Red bars indicate that a core is failing. Different shades of green indicate different
tasks. If a green execution is interupted by a red block, that job is lost.

Command Line:
The intervals will be printed to the command line, including which core was running, which job was running, and other useful information.
A check is made at the end to see whether all jobs met their deadlines. If not, the list of jobs that first exceeded their deadlines
(either primary or backups) will be printed.
