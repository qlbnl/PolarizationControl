import serial
import numpy as np


class EPCDriver(object):
    def __init__(self, port="/dev/ttyUSB1", baudrate=9600, debug=False):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE
            )
        except serial.serialutil.SerialException:
            self.ser = None
        self.debug = debug
        self.buflen = 2048
        self._ask("MDC")

    @property
    def okay(self):
        return True if self.ser else False

    def _ask(self, cmd):
        if self.ser:
            self.ser.write(f'{cmd}\r\n'.encode())
            if self.debug:
                print("rc: {rc} for {cmd}")
            return self.ser.read(self.buflen).decode()

    @property
    def help(self):
        return self._ask("?")

    def write_v(self, ch, value):
        value = int(value)
        if (value > 5000) or (value < -5000):
            value = 5000 * np.sign(value)
        else:
            command = f'V{ch},{value}\r\n'
            encoded_command = command.encode()
            self.ser.write(encoded_command)
        return 0
