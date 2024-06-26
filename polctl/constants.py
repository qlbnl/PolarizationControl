import numpy as np

WAVELENGTH = 1550e-9
STEP = 50  # min voltage resolution of EPC
LEARNING_RATE = 100
NCHAN = 4
EPC_SLEEP_TIME = 0.4  # seconds
DEF_CAP_SAMPLES = 10
DEF_CAP_SAMPLE_SLEEP = 0.5
DEF_GA_FIDELITY = 0.999
DEF_GA_ITERATIONS = 200
DEF_GA_RAND_THRESH = 0.75
DEF_GA_RAND_ITERS = 20

Hstate = np.array([1, 0, 0])
Vstate = np.array([-1, 0, 0])
Dstate = np.array([0, 1, 0])
ADstate = np.array([0, -1, 0])
Rstate = np.array([0, 0, 1])
Lstate = np.array([0, 0, -1])

MAX_BUFLEN = 512


class CMD:
    MEAS = "R"
    SET = "S"
    CAPTURE = "C"
    MAINTAIN = "M"
    TFORM = "T"
    GET = "G"
