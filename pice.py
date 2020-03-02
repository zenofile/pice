#!/usr/bin/env python3

import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from time import sleep
from typing import List, Tuple


@dataclass
class PiMon:
    '''Class for monitoring raspberry pi temperature and voltage levels'''
    proc_handle = None

    nr_reads: int = 0
    nr_throttles: int = 0

    mm_cpu_temp: list = None
    mm_gpu_temp: list = None
    mm_pkg_volts: list = None

    ptn_temp: str = None
    ptn_volts: str = None
    ptn_throttle: str = None

    def cpu_temp(self):
        if self.proc_handle is None or self.proc_handle.closed:
            self.proc_handle = open("/sys/class/thermal/thermal_zone0/temp",
                                    "r")
        else:
            self.proc_handle.seek(0)

        info = self.proc_handle.readline()
        cpu = None
        try:
            cpu = int(info) / 1000.0
        except ValueError:
            pass
        else:
            if self.mm_cpu_temp is None:
                self.mm_cpu_temp = [cpu] * 2
            else:
                self.mm_cpu_temp = [
                    min(cpu, self.mm_cpu_temp[0]),
                    max(cpu, self.mm_cpu_temp[1])
                ]
        return cpu

    def is_throttled(self) -> bool:
        buf = PiMon.__exec_command('get_throttled')
        if self.ptn_throttle is None:
            self.ptn_throttle = re.compile("throttled=")
        val = self.ptn_throttle.split(buf)[1]
        bits = None
        try:
            bits = int(val, 0)
        except ValueError:
            return None
        throttled = False if bits == 0 else True
        return throttled

    def gpu_temp(self) -> float:
        buf = PiMon.__exec_command('measure_temp')
        if self.ptn_temp is None:
            self.ptn_temp = re.compile("temp=|'")
        val = self.ptn_temp.split(buf)[1]
        gpu = None
        try:
            gpu = float(val)
        except ValueError:
            pass
        else:
            if self.mm_gpu_temp is None:
                self.mm_gpu_temp = [gpu] * 2
            else:
                self.mm_gpu_temp = [
                    min(gpu, self.mm_gpu_temp[0]),
                    max(gpu, self.mm_gpu_temp[1])
                ]
        return gpu

    def pkg_voltage(self) -> float:
        buf = PiMon.__exec_command('measure_volts')
        if self.ptn_volts is None:
            self.ptn_volts = re.compile("volt=|V")
        val = self.ptn_volts.split(buf)[1]
        pkg = None
        try:
            pkg = float(val)
        except ValueError:
            pass
        else:
            if self.mm_pkg_volts is None:
                self.mm_pkg_volts = [pkg] * 2
            else:
                self.mm_pkg_volts = [
                    min(pkg, self.mm_pkg_volts[0]),
                    max(pkg, self.mm_pkg_volts[1])
                ]
        return pkg

    def read_data(self) -> Tuple[float, float, float, bool]:
        self.nr_reads += 1
        throttle = self.is_throttled()
        if throttle == True: self.nr_throttles += 1
        return (self.cpu_temp(), self.gpu_temp(), self.pkg_voltage(), throttle)

    @staticmethod
    def __exec_command_pipe(command: str) -> str:
        out = subprocess.Popen(['vcgencmd', command],
                               stdout=subprocess.PIPE).communicate()
        return out[0].decode('utf-8')
        
    @staticmethod
    def __exec_command(command: str) -> str:
        out = subprocess.check_output(['vcgencmd', command])
        return out.decode('utf-8')
        
    @classmethod
    def format_celsius(cls, temp: float) -> str:
        return '{:>+4.1f}°C'.format(temp)

    @classmethod
    def format_volts(cls, volts: float) -> str:
        return '{:>4.4f}V'.format(volts)

    def __str__(self) -> str:
        row_fmt = '\033[1m{:>8}\033[0m' * 3 + '\n'
        buf = row_fmt.format('Summary', 'min', 'max')
        row_fmt = '{:<8}' + '{:>+8.1f}' * 2 + '\n'
        buf += row_fmt.format('CPU (°C)', *self.mm_cpu_temp)
        buf += row_fmt.format('GPU (°C)', *self.mm_gpu_temp)
        row_fmt = '{:<8}' + '{:>8.4f}' * 2 + '\n'
        buf += row_fmt.format('PKG ( V)', *self.mm_pkg_volts)

        buf += '\n{:>10} {:d}\n'.format('Throttles:', self.nr_throttles)
        buf += '{:>10} {:d}\n'.format('Samples:', self.nr_reads)
        return buf

    def __exit__(self, *args):
        self.proc_handle.close()


def main():
    interval: float = 2.0
    n: int = -1
    args = sys.argv[1:]
    num_args = len(args)

    if args:
        try:
            interval = float(args[0])
        except ValueError:
            pass
        if num_args > 1:
            try:
                n = int(args[1])
            except ValueError:
                print("Wrong parameter format.", file=sys.stderr)
                sys.exit(1)

    mon = PiMon()

    def summary(obj: PiMon):
        print('\n\n{:}'.format(obj))

    def signal_handler(signal, frame):
        summary(mon)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        if n > 0: n -= 1
        data = mon.read_data()

        if None not in data:
            print('CPU: {:}'.format(PiMon.format_celsius(data[0])), end=' ')
            print('\tGPU: {:}'.format(PiMon.format_celsius(data[1])), end=' ')
            if data[3] == True:
                print('\tVcore: {:}'.format(PiMon.format_volts(data[2])),
                      end=" ")
                print('\tThrottled: True')
            else:
                print('\tVcore: {:}'.format(PiMon.format_volts(data[2])))

        if n == 0:
            summary(mon)
            break

        sleep(interval)


if __name__ == '__main__':
    main()
