import pyvisa as visa
from cmath import cos, sin


class PAX1000(object):
    def __init__(self, device='USB0::4883::32817::M00937524::0::INSTR'):
        # pyvisa-py
        rm = visa.ResourceManager('@py')

        # NI-ViSA
        # rm = visa.ResourceManager()

        print(rm)
        print(rm.list_resources("?*"))
        # pybisa-py
        self.inst = rm.open_resource(
            resource_name=device, write_termination='\n', read_termination='\n')

        # NI-VISA
        # self.inst = rm.open_resource(device=device)

    def reset(self):
        # Returns the unit to the *RST default condition
        self.inst.write('*RST')

    def clear(self):
        # Clears all event registers and Error Queue
        self.inst.write('*CLS')

    def qry(self):
        # Returns the unit's identification string
        return self.inst.query('*IDN?')

    def wavelength(self):
        # Returns wavelength in [m]
        return self.inst.query(
            'SENS:CORR:WAV?')

    def mode(self):
        return self.inst.query('SENS:DATA:LAT?').strip('\n').split(',')[2]
        # 0:revs, 1:timestamp, 2:paxOpMode, 3:paxFlags (s. Kap. 3.6.4.2.3.1), 4:paxTIARange, 5:adcMin, 6:adcMax,
        # 7:revTime, 8:misAdj, 9:theta, 10:eta, 11:DOP, 12:Ptotal

    def measure(self):
        return self.inst.query(
            'SENS:DATA:LAT?').strip('\n').split(',')

    def DOP(self):
        return float(self.inst.query(
            'SENS:DATA:LAT?').strip('\n').split(',')[11])*100

    def total_power(self):
        return float(self.inst.query(
            'SENS:DATA:LAT?').strip('\n').split(',')[12])

    def write(self, cmd):
        self.inst.write(cmd)

    def stoke_vectors(self):
        li = self.measure()
        psi = float(li[9])
        chi = float(li[10])
        S1 = cos(2*psi)*cos(2*chi)  # normalized S1
        S2 = sin(2*psi)*cos(2*chi)  # normalized S2
        S3 = sin(2*chi)             # normalized S3
        return [S1, S2, S3]

    def inp_wav(self, wavelength):     # range -> (900 - 1700)nm
        self.inst.write(f'SENS:CORR:WAV {float(wavelength)};:INP:ROT:STAT 1')
