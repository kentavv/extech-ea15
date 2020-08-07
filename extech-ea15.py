#!/usr/bin/env python

# Copyright 2020 Kent A. Vander Velden <kent.vandervelden@gmail.com>
#
# If you use this software, please consider contacting me. I'd like to hear
# about your work.
#
# This file is part of Extech-EA15, a decoder for the Extech EA15 thermocouple
# datalogging thermometer.
#
# Please see LICENSE for limitations on use.
#
# If you see a permission problem with accessing serial ports, the following may help.
# Add yourself to the dialout group and remove modemmanager.
# $ adduser kent dialout
# $ apt remove modemmanager

import datetime
import multiprocessing as mp
import time

import serial


class Temperature:
    v_ = 0
    valid_ = False

    def __init__(self, v=None, u='C'):
        if v is not None:
            self.set(v, u)

    def __str__(self):
        return f'{self.v_:.02f}C'

    def set(self, v, u='C'):
        self.valid_ = True
        if u == 'C':
            self.v_ = v
        elif u == 'F':
            self.v_ = self.f2c(v)
        elif u == 'K':
            self.v_ = self.k2c(v)
        else:
            self.valid_ = False

    def C(self):
        return self.v_

    def F(self):
        return self.c2f(self.v_)

    def K(self):
        return self.c2k(self.v_)

    @staticmethod
    def f2c(v):
        return (v - 32) * (5 / 9.)

    @staticmethod
    def k2c(v):
        return v - 273.15

    @staticmethod
    def c2f(v):
        return v * (9 / 5.) + 32

    @staticmethod
    def c2k(v):
        return v + 273.15


class ExtechEA15Serial:
    ser = None
    download_datalog_ = False

    def __init__(self, dev_fn=''):
        self.open(dev_fn)

    def __del__(self):
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

    def open(self, dev_fn):
        self.ser = serial.Serial(dev_fn, 9600, timeout=2)

    def decode(self, buf, dt=None):
        d = {'dt': datetime.datetime.now() if dt is None else dt,
             't1': Temperature(),
             't1u': '',
             't2': '',
             't2u': '',
             'type': '',
             'valid': False
             }

        d2 = {'dt': d['dt'],
              't1': Temperature(),
              't2': Temperature(),
              'type': '',
              'valid': False
              }

        if not (buf[0] == 0x02 and buf[-1] == 0x03 and len(buf) == 9):
            return d2

        temp_units = {0: 'C', 2: 'K', 3: 'F'}
        sensor_types = {0: 'K', 1: 'J', 2: 'E', 3: 'T', 4: 'R', 5: 'S', 6: 'N'}

        d['t1'] = (buf[2] * 0xff + buf[3]) / 10.
        d['t1u'] = temp_units[buf[1]]
        d['t2'] = (buf[5] * 0xff + buf[6]) / 10.
        d['t2u'] = temp_units[buf[4]]
        d['type'] = sensor_types[buf[7]]

        d['valid'] = True

        d2 = {'dt': d['dt'],
              't1': Temperature(d['t1'], d['t1u']),
              't2': Temperature(d['t2'], d['t2u']),
              'type': d['type'],
              'valid': d['valid'],
              }

        return d2

    def decode2(self, buf, start_dt):
        if not (buf[0] == 0x02 and buf[-1] == 0x03):
            return []

        all_lst = []

        i = 1
        s = 0
        sps = 0
        lst = []
        marker = b'\x00\x55\xaa\x00'
        while True:
            if s == 0:
                if len(buf) <= i + 5:
                    break
                if buf[i:i + 4] == marker:
                    s = 1
                    sps = buf[i + 4]
                    i += 5
                else:
                    i += 1
            else:
                if len(buf) <= i + 7:
                    break
                if buf[i:i + 4] == marker:
                    all_lst += [(sps, lst)]
                    lst = []
                    sps = buf[i + 4]
                    i += 5
                else:
                    bb = buf[i:i + 7]
                    bb = b'\x02' + bb + b'\x03'
                    lst += [self.decode(bb, start_dt + datetime.timedelta(seconds=i * sps))]
                    i += 7

        if i + 1 != len(buf):
            print(f'Truncated download: {i + 1} {len(buf)}')

        if lst:
            all_lst += [(sps, lst)]

        return all_lst

    datalog_download_state_ = 0

    def decode_one(self):
        s = 0
        buf = []
        while True:
            if self.download_datalog_ and self.datalog_download_state_ == 0:
                self.datalog_download_state_ = 1
                self.download_datalog_ = False

            c = self.ser.read()
            # There's also .read_until(0x03)
            if c == b'':
                return None

            if False:
                if self.datalog_download_state_ == 1:
                    if time.time() - s2_t > 2:
                        print('a')
                        self.ser.write(b'\x41')
                        # ser.write(b'\x41')
                        self.ser.flush()
                        s2_t = time.time()
                elif self.datalog_download_state_ == 2:
                    print('b')
                    self.ser.write(b'\x55')
                    self.ser.flush()

            if s == 0 and c[0] == 0x02:
                s = 1
                buf = c
            elif s == 1 and c[0] == 0x03:
                buf += c

                if self.datalog_download_state_ == 1:
                    time.sleep(.01)
                    self.ser.write(b'\x41')
                    self.ser.flush()
                elif self.datalog_download_state_ == 2:
                    time.sleep(.01)
                    self.ser.write(b'\x55')
                    self.ser.flush()

                if len(buf) == 9:
                    return self.decode(buf)
                elif len(buf) == 5:
                    # print(buf)
                    # 02 00 8c 80 03 <= empty datalog 35968
                    # 02 00 8c 8c 03 <= 1 datalog entry 35980 12 = 1*5 + 1*7
                    # 02 00 8c 93 03 <= 2 datalog entries 35987 19 = 1*5 + 2*7
                    # 02 00 8c a1 03 <= 4 datalog entries 36001 33 = 1*5 + 4*7
                    # 02 00 8c c9 03 <= 2 sets with 1 and 8 records 36041 73 = 2*5 + 9*7
                    # 02 00 8d 57 03 <= 30 datalog entries 36183 215 = 1*5 + 30*7
                    n = buf[2] * 256 + buf[3] - 0x8c80
                    if n == 0:
                        print(f'Datalog is empty')
                        self.datalog_download_state_ = 0
                    else:
                        print(f'Expecting {n} bytes from datalog')
                        self.datalog_download_state_ = 2
                elif buf.startswith(b'\x02\x00\x55\xaa\x00'):
                    self.datalog_download_state_ = 0
                    return self.decode2(buf, datetime.datetime.now())
                else:
                    print('Unable to decode:', buf)

                buf = b''
            elif s == 1:
                buf += c

    def decode_loop(self):
        while True:
            v = self.decode_one()
            if v is None:
                continue
            print(v)

    def download_datalog(self):
        if self.datalog_download_state_ == 0:
            self.download_datalog_ = True


class ExtechEA15Threaded:
    q = None
    q2 = None
    q3 = None
    ea15 = None
    download_datalog_ = False
    dev_fn_ = ''

    def __init__(self, dev_fn=''):
        self.q = mp.Queue()
        self.q2 = mp.Queue()
        self.q3 = mp.Queue()
        self.dev_fn_ = dev_fn
        self.ea15 = ExtechEA15Serial(dev_fn)

    def __del__(self):
        pass

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, type, value, tb):
        pass

    def open(self, dev_fn):
        self.ea15.open(dev_fn)

    def run(self):
        p = mp.Process(target=self.main, args=(self,))
        p.start()

    def main(self_, self):
        # self.ea15 = ExtechEA15(self.dev_fn_)
        while True:
            if not self.q3.empty():
                s = self.q3.get()
                if s == 'Datalog':
                    self.ea15.download_datalog()

            v = self.ea15.decode_one()
            if v is None:
                pass
            elif isinstance(v, dict):
                self.q.put(v)
            elif isinstance(v, list):
                self.q2.put(v)

    def download_datalog(self):
        self.q3.put('Datalog')


def main(dev_fn):
    def decode(v):
        return f'{v["dt"]} : {v["t1"]} : {v["t2"]} : {v["type"]} : {v["valid"]}'

    # Below are a few different ways to use the classes

    if False:
        with ExtechEA15Serial(dev_fn) as ea15:
            ea15.decode_loop()

    if False:
        with ExtechEA15Serial(dev_fn) as ea15:
            for i in range(3):
                print(i, ea15.decode_one())

    if False:
        ea15 = ExtechEA15Serial(dev_fn)
        print(ea15.decode_one())

    if False:
        ea15 = ExtechEA15Threaded(dev_fn)
        ea15.run()
        while True:
            while not ea15.q.empty():
                v = ea15.q.get()
                print(decode(v))

    if True:
        with ExtechEA15Threaded(dev_fn) as ea15:
            import time, random

            while True:
                while not ea15.q.empty():
                    v = ea15.q.get()
                    print(decode(v))
                # import queue
                # try:
                #     v = ea15.q.get(timeout=.05)
                #     print('dequeued', v)
                # except queue.Empty:
                #     print('timeout')

                if random.random() < .05:
                    print('Requesting datalog download')
                    ea15.download_datalog()

                while not ea15.q2.empty():
                    v2_ = ea15.q2.get()
                    for j, v2 in enumerate(v2_):
                        sps, lst = v2
                        print(f'Datalog set {j} with {len(lst)} records, sampled every {sps} seconds')
                        for i, v in enumerate(lst):
                            v['dt'] = i * sps
                            print(f'{i:04d} : {decode(v)}')

                time.sleep(.5)


if __name__ == "__main__":
    main('/dev/ttyUSB0')
