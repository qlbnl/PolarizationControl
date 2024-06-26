import numpy as np
from polctl.constants import (
    DEF_GA_FIDELITY,
    DEF_GA_ITERATIONS,
    CMD
)


class GAParams:
    def __init__(self, args, cap, ttarget):
        self._targets = list()
        self._fidelity = DEF_GA_FIDELITY
        self._iters = DEF_GA_ITERATIONS
        self._time_limit = None

        if not args:
            raise Exception("No arguments")
        else:
            self._set_params(args, cap, ttarget)

    def _set_params(self, args, cap, ttarget):
        p0 = args[0]
        if p0 == CMD.CAPTURE:
            if cap is None:
                raise LookupError("No SOP capture set, issue 'C' command first")
            else:
                self._targets.append(cap)
        elif p0 == CMD.TFORM:
            if ttarget is None:
                raise LookupError("No transform target is set, issue 'T' command first")
            else:
                self._targets.append(ttarget)
        else:
            try:
                stokes = p0.split(",")
                if len(stokes) != 3:
                    raise Exception("Invalid SOP as Stokes params, should be S1,S2,S3")
                self._targets.append(np.array(list(map(float, p0.split(",")))))
            except Exception as e:
                raise e
        try:
            self._fidelity = float(args[1])
            self._iters = int(args[2])
            self._time_limit = int(args[3])
        except Exception:
            pass

    @property
    def target_states(self):
        return self._targets

    @property
    def fidelity(self):
        return self._fidelity

    @property
    def iters(self):
        return self._iters

    @property
    def time_limit(self):
        return self._time_limit
