import sys
import time
import asyncio
import logging
import numpy as np
from polctl.ga_params import GAParams
from polctl.pax1000 import PAX1000
from polctl.ozoptics import EPCDriver
from polctl.sop import transform
from polctl.constants import (
    MAX_BUFLEN,
    CMD,
    WAVELENGTH,
    DEF_CAP_SAMPLES,
    DEF_CAP_SAMPLE_SLEEP,
    DEF_GA_RAND_ITERS,
    DEF_GA_RAND_THRESH,
    STEP,
    NCHAN,
    LEARNING_RATE,
    EPC_SLEEP_TIME,
    Hstate
)


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

lock = asyncio.Lock()
sq = asyncio.Queue()
rq = asyncio.Queue()


class PolarizationControl:
    def __init__(self, pinit=None):
        # cmd state
        self._curcmd = CMD.MEAS
        self._curargs = None
        self._prevcmd = CMD.MEAS
        self._prevargs = None
        # Initial SOP parameters
        self._pinit = pinit
        self._phist = None
        self._cap = None
        self._ttarget = None
        self._sop = None
        # Initializing EPC driver and Polarimeter
        self.epc = EPCDriver()
        self.pax = PAX1000()
        # Check if EPC and Polarimeter are accessible
        if not self.epc.okay:
            raise Exception("EPC device is not accessible!")
        if self.pax.qry() != "THORLABS,PAX1000IR2,M00937524,1.0.13":
            raise Exception("Polarimeter device is not accessible!")
        # Print initial information
        # 2 revolutions for one measurement, 2048 points for FFT
        self.pax.write(cmd='SENS:CALC 9;:INP:ROT:STAT 1')
        # set measurement wavelength for polarimeter
        log.info(f"Mode: {self.pax.mode()}")
        # set measurement wavelength for polarimeter, depends on the input laser source
        self.pax.inp_wav(wavelength=WAVELENGTH)
        wav = self.pax.wavelength()
        log.info(f"Wavelength: {wav}")

    def _prev_cmd(self):
        self._curcmd = self._prevcmd
        self._curargs = self._prevargs

    def _reset_cmd(self):
        self._curcmd = CMD.MEAS
        self._curargs = None

    async def _get_cmd(self):
        new = True
        try:
            msg = rq.get_nowait()
            self._prevcmd = self._curcmd
            self._prevargs = self._curargs
            self._curcmd = msg.get("cmd")
            self._curargs = msg.get("args")
            log.info(f"cmd: {self._curcmd}, args: {self._curargs}")
        except asyncio.QueueEmpty:
            new = False
        return self._curcmd, self._curargs, new

    async def _handle_get(self, cmd, args):
        if args[0] == CMD.CAPTURE:
            return f"OK {self._cap}"
        elif args[0] == CMD.TFORM:
            return f"OK {self._ttarget}"
        elif args[0] == "SOP":
            if self._cap is not None:
                inner_product = (self._sop*self._cap).sum()
                return f"OK {self._sop} f={float(inner_product.real)}"
            else:
                return f"OK {self._sop}"
        else:
            return "ERR UNKNOWN_ARGS"

    async def _handle_transform(self, cmd, args):
        if not args:
            log.error("No argument given, specify theta")
            return "ERR NO_ARGS"
        if self._cap is None:
            log.error("No captured SOP to transform, capture first")
            return "ERR NO_CAP"
        try:
            self._ttarget = transform(self._cap, int(args[0]))
            log.info(f"Calculated new target SOP: {self._ttarget}")
            return f"OK {self._ttarget}"
        except Exception as e:
            log.error(f"Could not transform: {e}")
            return "ERR EXCEPTION"

    async def _handle_meas(self, cmd, args, maintain=False):
        inner_product = "N/A"
        v = np.array(self.pax.stoke_vectors())
        self._sop = v

        if maintain and not args:
            log.error("No argument given, specify maintain target")
            return "ERR NO_ARGS"

        if args:
            try:
                params = GAParams(args, self._cap, self._ttarget)
            except LookupError as e:
                log.error(f"{e}")
                return "ERR NOT_SET"
            except Exception as e:
                log.error(f"Could not get GA params: {e}")
                return "ERR PARSE_FAIL"
            inner_product = (v*params.target_states).sum()

        if maintain and inner_product < params.fidelity:
            try:
                p_history, f_history, iter = await self.gradient_ascent(
                    target_states=params.target_states,
                    target_pols=None,
                    max_iterations=params.iters,
                    threshold=(1-params.fidelity),
                    paramsi=None,
                    channels=[1, 1, 1, 1])
            except Exception as e:
                log.error(f"Could not complete GA: {e}")
                return f"ERR {e}"
            log.info(f"[Maintain] Current f: {f_history[-1]}")
            ret = f"OK {f_history[-1]}"
        elif maintain:
            log.info(f"[Maintain] Current f: {inner_product}")
            ret = f"OK {inner_product}"
        else:
            log.info(f"Stokes: {v}, f = {inner_product}")
            ret = f"OK {inner_product}"
        return ret

    async def _handle_ga(self, cmd, args, pinit=None):
        if not args:
            log.error("No SOP arguments provided")
            return "ERR NO_ARGS"
        try:
            params = GAParams(args, self._cap, self._ttarget)
        except LookupError as e:
            log.error(f"{e}")
            return "ERR NOT_SET"
        except Exception as e:
            log.error(f"Could not get GA params: {e}")
            return "ERR PARSE_FAIL"
        try:
            p_history, f_history, iter = await self.gradient_ascent(
                target_states=params.target_states,
                target_pols=None,
                max_iterations=params.iters,
                threshold=(1-params.fidelity),
                paramsi=pinit,
                channels=[1, 1, 1, 1])
        except Exception as e:
            log.error(f"Could not complete GA: {e}")
            return f"ERR {e}"
        result = float(f_history[-1][0].real)
        log.info(f"Result: {result}")
        return f"OK {result}"

    async def _handle_capture(self, cmd, args):
        samples = DEF_CAP_SAMPLES
        if args:
            try:
                samples = int(args[0])
            except Exception as e:
                log.error(f"Invalid args: {e}")
                return self._cap
        log.info(f"Capturing {samples} SOPs...")
        ary = np.array([0j, 0j, 0j])
        for i in range(1, samples+1):
            v = np.array(self.pax.stoke_vectors())
            log.info(f"{i}: {v}")
            ary += v
            await asyncio.sleep(0.01)
            time.sleep(DEF_CAP_SAMPLE_SLEEP)
        ary /= samples
        self._cap = ary
        log.info(f"Mean SOP after {samples} readings: {ary}")
        return f"OK {ary}"

    async def _loop(self):
        while True:
            log.info(f"({self._curcmd}) Polarimeter power: {self.pax.total_power()}")
            cmd, args, change = await self._get_cmd()
            if cmd == CMD.MEAS:
                ret = await self._handle_meas(cmd, args)
            elif cmd == CMD.SET:
                ret = await self._handle_ga(cmd, args)
                self._reset_cmd()
            elif cmd == CMD.CAPTURE:
                ret = await self._handle_capture(cmd, args)
                self._prev_cmd()
            elif cmd == CMD.MAINTAIN:
                ret = await self._handle_meas(cmd, args, maintain=True)
            elif cmd == CMD.TFORM:
                ret = await self._handle_transform(cmd, args)
                self._prev_cmd()
            elif cmd == CMD.GET:
                ret = await self._handle_get(cmd, args)
                self._prev_cmd()
            else:
                log.error(f"Unknown command: {cmd}")
                ret = "ERR UNKNOWN_CMD"
                self._prev_cmd()
            if change:
                await sq.put(f"{ret}")
            await asyncio.sleep(1)

    def _rand_params(self, channels=[1]*NCHAN):
        p = (np.random.rand(4) - 0.5) * 9900
        for i, v in enumerate(channels):
            p[i] = 0 if not v else p[i]
        return p

    async def gradient_ascent(self, target_states=[Hstate], target_pols=[], max_iterations=400,
                              threshold=0.01, paramsi=None, channels=[1]*NCHAN):
        if paramsi is not None:
            params0 = paramsi
            log.debug(f"Initial params: {params0}")
        elif self._phist is not None:
            params0 = self._phist
        else:
            params0 = self._rand_params(channels=channels)
        log.info(f"Checking random search for initial threshold {DEF_GA_RAND_THRESH}")
        attempts = DEF_GA_RAND_ITERS
        while True:
            inner_curr = self.read_inner(params0, target_states, target_pols)
            log.info(f"f = {inner_curr}")
            log.debug(f"targets: {target_states}")
            log.debug(f"params0: {params0}")
            if inner_curr > DEF_GA_RAND_THRESH:
                break
            params0 = self._rand_params(channels=channels)
            attempts -= 1
            if not attempts:
                raise Exception("Random search failure")
        # Set gradient step, initialize parameters and history
        grad_step = STEP
        p = params0.copy()
        pgrad = params0.copy()
        p_history = p
        f_history = inner_curr
        diff = 1.0e10  # 1
        log.info("Starting GA search...")
        for iters in range(max_iterations):
            if diff < threshold:
                break
            gchange = False
            while not gchange:
                for i, v in enumerate(channels):
                    if v and np.random.rand() > 0.5:
                        pgrad[i] += grad_step
                        gchange = True
            (pgrad, inner_curr) = self.grad_func(p, pgrad, target_states, target_pols,
                                                 LEARNING_RATE, inner_curr)
            p = pgrad.copy()
            p[p > 5000] = 0
            p[p < -5000] = 0
            p_history = np.vstack((p_history, p))
            f_history = np.vstack((f_history, inner_curr))
            log.info(f"Iter {iters+1}, f = {float(f_history[-1][0].real)} - {np.round(p)}")
            diff = np.absolute(f_history[-1] - 1)
            await asyncio.sleep(0.01)
        self._phist = p_history[-1]
        return p_history, f_history, iters+1

    def read_inner(self, params, target_states, input_pols):
        ret_f = 0
        nstates = len(target_states)
        for i, tstate in enumerate(target_states):
            for ch in range(len(params)):
                self.epc.write_v(ch+1, params[ch])
            time.sleep(EPC_SLEEP_TIME)
            # calculate inner product by normalized Stokes vector, format is (S1, S2, S3)
            inner_product = (np.array(self.pax.stoke_vectors())*tstate).sum()
            log.debug(f"\tinner ({tstate.tolist()}): {inner_product}")
            ret_f += inner_product/nstates
        return ret_f

    def grad_func(self, params0, params1, target_states, input_pols, learning_rate, inner_prev=None):
        if not inner_prev:
            inner_prev = self.read_inner(params0, target_states, input_pols)
        inner_adv = self.read_inner(params1, target_states, input_pols)
        # since calculating gradient is the most expensive operation here,
        # we will advance the state directly while calculating inner product
        # cost function is given by the deviation of inner product and 1
        delta_p = -(params1 - params0) * (abs(1 - inner_adv) -
                                          abs(1 - inner_prev)) * learning_rate
        if (inner_adv - inner_prev) < 0:
            params0 += delta_p
            inner_curr = self.read_inner(params0, target_states, input_pols)
            return (params0, inner_curr)  # if inner product decreases, advance from the previous direction
        else:
            params1 += delta_p
            inner_curr = self.read_inner(params1, target_states, input_pols)
            return (params1, inner_curr)  # if inner product increases, advance directly


# This method implements the socket server.
# It writes received commands from the network into a queue
async def PolControlProtocol(reader, writer):
    async def _write(val):
        val += "\n"
        writer.write(bytes(val, "utf-8"))
        await writer.drain()

    async def _try_lock(lock, attempts=2):
        while attempts:
            if lock.locked():
                await asyncio.sleep(1)
                attempts -= 1
            else:
                return True
        return False

    while True:
        data = await reader.read(MAX_BUFLEN)
        if not data:
            break
        if not await _try_lock(lock):
            await _write("ERR BUSY")
            continue
        await lock.acquire()
        try:
            msg = data.decode().strip().split(" ")
            cmd = msg[0]
            args = msg[1:] if len(msg) > 1 else None
            await rq.put({"cmd": cmd, "args": args})
            await _write(await sq.get())
        except Exception as e:
            log.error(f"Error processing request: {data}: {e}")
        lock.release()


async def run(pctl, host, port):
    server = await asyncio.start_server(PolControlProtocol, host, port)
    asyncio.create_task(pctl._loop())
    await server.serve_forever()


def main():
    try:
        pinit = sys.argv[1]
        pinit = np.array(list(map(float, pinit.split(","))))
    except Exception:
        pinit = None
    p = PolarizationControl(pinit)
    asyncio.run(main(p, '127.0.0.1', 6000))


if __name__ == '__main__':
    main()
