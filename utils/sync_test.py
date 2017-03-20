import matplotlib.pyplot as plt
import random

clamp = lambda v, l, h : max((min((v, h)), l))

PULSE_FREQUENCY = 120.0 # Hz
DUTY_CYCLE = 0.05 # Proportion of time spent high

SIGNAL_PERIOD = 1 / PULSE_FREQUENCY

DURATION = 2.0 # Seconds
SUBDIVISION = 100000.0 # Number of samples in a second

## Define some basic DSP functions
u = lambda t : 1 if t > 0 else 0
rect = lambda t,w,o : u(t-o) * u(w-(t-o))

## Define a timer to test synchronization algorithms with
class Timer(object):
    def __init__(self, period, start_count = 0):
        self.count = start_count
        self.period = period
        self.ignore_next = False

    def tick(self):
        if (self.count == self.period):
            self.count = 0
            if self.ignore_next:
                self.ignore_next = False
                return 0
            return 1
        self.count += 1
        return 0

    def zone(self, zones):
        for i,zone in enumerate(zones):
            if float(self.count) / self.period < zone:
                return i
        return len(zones)

    def offsetPhase(self, offset):
        # If we're offsetting backwards, we don't want to trip the output right away...
        if (offset < 0):
            self.ignore_next = True
        self.count = (self.count + offset) % (self.period + 1)

## Define a timebase
xs = [x / SUBDIVISION for x in range(int(SUBDIVISION * DURATION))]

## Generate a signal from the timebase
#signal = lambda t : rect(t % (1.0 / PULSE_FREQUENCY), (DUTY_CYCLE / PULSE_FREQUENCY), 0)

DUTY_ERROR = 0.1
SWEEP_WIDTH = 0.05

period_num = 0
deviation_positive = deviation_negative = SIGNAL_PERIOD * DUTY_CYCLE / 2

signal_trace = []

sweep_center = 0.5

for t in xs:
    modt = t % SIGNAL_PERIOD
    test_period_num = int(t / SIGNAL_PERIOD)

    if modt < deviation_positive or modt > (SIGNAL_PERIOD - deviation_negative) or (modt > (SIGNAL_PERIOD * (sweep_center - SWEEP_WIDTH)) and modt < (SIGNAL_PERIOD * (sweep_center + SWEEP_WIDTH))):
        signal_trace.append(1)
    else:
        signal_trace.append(0)

    if test_period_num != period_num:
        deviation_positive = (1 + random.random() * DUTY_ERROR - DUTY_ERROR / 2) * DUTY_CYCLE / 2 * SIGNAL_PERIOD
        deviation_negative = (1 + random.random() * DUTY_ERROR - DUTY_ERROR / 2) * DUTY_CYCLE / 2 * SIGNAL_PERIOD
        sweep_center = clamp(sweep_center + (random.random() - 0.5) / 10, 0, 1)
        period_num = test_period_num


zones = [DUTY_CYCLE * 2, 1 - (DUTY_CYCLE * 2)]
error_accums = [0, 0, 0]
timer = Timer(int(1.0 / PULSE_FREQUENCY * SUBDIVISION))
timer.offsetPhase(int(random.random() * timer.period))

#signal_trace = [signal(x) for x in xs]
timer_trace = []
accum_traces = []
timer_count_trace = []



for a in error_accums:
    accum_traces.append([])

for t,s in zip(xs, signal_trace):
    timer_match = timer.tick()
    timer_count_trace.append(timer.count)
    timer_trace.append(timer_match)

    error_accums[timer.zone(zones)] += s

    for i in range(len(error_accums)):
        accum_traces[i].append(error_accums[i])

    if(timer_match):
        offset = (
            (error_accums[2] - error_accums[0]) / 2 +
            (1 if error_accums[1] else 0) +
            ((timer.period / 4) if abs(error_accums[2] - error_accums[0]) > int(timer.period * DUTY_CYCLE * 2) else 0) +
            ((timer.period / 8) if abs(error_accums[2] + error_accums[0]) < int(timer.period * DUTY_CYCLE / 2) else 0)
            )
        timer.offsetPhase(offset)
        error_accums = [0] * (len(zones) + 1)

for trace in [signal_trace, timer_trace] + accum_traces:
    trace_max = max(trace)

    if trace_max == 0:
        trace_max = 1
    norm_trace = [t / float(trace_max) for t in trace]

    plt.plot(xs, norm_trace)

plt.show()
