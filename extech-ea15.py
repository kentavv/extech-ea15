#!/usr/bin/env python

import datetime
import multiprocessing as mp
import queue

import serial


class ExtechEA15:
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
             't1': '',
             't1u': '',
             't2': '',
             't2u': '',
             'type': '',
             'valid': False
             }

        if not (buf[0] == 0x02 and buf[-1] == 0x03 and len(buf) == 9):
            return d

        temp_units = {0: 'C', 2: 'K', 3: 'F'}
        sensor_types = {0: 'K', 1: 'J', 2: 'E', 3: 'T', 4: 'R', 5: 'S', 6: 'N'}

        d['t1'] = (buf[2] * 0xff + buf[3]) / 10.
        d['t1u'] = temp_units[buf[1]]
        d['t2'] = (buf[5] * 0xff + buf[6]) / 10.
        d['t2u'] = temp_units[buf[4]]
        d['type'] = sensor_types[buf[7]]

        d['valid'] = True

        return d

    def decode2(self, buf, start_dt):
        lst = []

        if not (buf[0] == 0x02 and buf[-1] == 0x03 and ((len(buf) - 2 - 3 - 2) % 7 == 0)):
            return 0, lst

        a = buf[1]
        b = buf[2] * 0xff + buf[3]
        c = buf[4]
        sps = buf[5]

        for i, s in enumerate(range(6, len(buf) - 1, 7)):
            bb = buf[s:s + 7]
            bb = b'\x02' + bb + b'\x03'
            lst += [self.decode(bb, start_dt + datetime.timedelta(seconds=i * sps))]

        return sps, lst

    def decode_one(self):
        s = 0
        s2 = 0
        buf = []
        while True:
            if self.download_datalog_ and s2 == 0:
                s2 = 1

            c = self.ser.read()
            # There's also .read_until(0x03)
            if c == b'':
                return None

            # print(s, s2, c)

            if s2 == 1:
                self.ser.write(b'\x41\x41')
                # ser.write(b'\x41')
                self.ser.flush()
            elif s2 == 2:
                self.ser.write(b'\x55\x55')
                self.ser.flush()

            if s == 0 and c[0] == 0x02:
                s = 1
                buf = c
            elif s == 1 and c[0] == 0x03:
                buf += c
                # print(buf)
                # print(buf[0])
                # print('buf_len:', len(buf), s2)
                if len(buf) == 9:
                    return self.decode(buf)
                    # if s2 == 1:
                    #     s2 = 2
                elif len(buf) == 5:
                    print(buf)
                    s2 = 2
                elif s2 in [1, 2]:
                    return self.decode2(buf, datetime.datetime.now())
                    s2 = 0

                buf = b''
            elif s == 1:
                buf += c

    def decode_loop(self):
        while True:
            v = self.decode_one()
            if v is None:
                continue
            print(v)

    def download_catalog(self):
        self.download_datalog_ = True


class ExtechEA15b:
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
        self.ea15 = ExtechEA15(dev_fn)

    def __del__(self):
        pass

    def __enter__(self):
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
                print('hi')
                s = self.q3.get()
                if s == 'Datalog':
                    self.ea15.download_catalog()

            v = self.ea15.decode_one()
            if v is None:
                pass
            elif isinstance(v, dict):
                self.q.put(v)
            elif isinstance(v, tuple):
                self.q2.put(v)

    def download_datalog(self):
        self.q3.put('Datalog')


def main(dev_fn):
    # with ExtechEA15(dev_fn) as ea15:
    #     ea15.decode_loop()

    # with ExtechEA15(dev_fn) as ea15:
    #     for i in range(3):
    #         print(i, ea15.decode_one())

    # ea15 = ExtechEA15(dev_fn)
    # print(ea15.decode_one())

    ea15 = ExtechEA15b(dev_fn)
    ea15.run()

    while True:
        try:
            v = ea15.q.get(timeout=.05)
            print('dequeued')
        except queue.Empty:
            print('timeout')

        ea15.download_datalog()
        v2 = ea15.q2.get()
        print('dequeued', v2)


if __name__ == "__main__":
    main('/dev/ttyUSB0')
