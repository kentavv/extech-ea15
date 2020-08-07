#!/usr/bin/env python

import serial
import datetime

def decode(buf, dt=None):
    d = { 'dt': datetime.datetime.now() if dt is None else dt,
          't1': '',
          't1u': '',
          't2': '',
          't2u': '',
          'type': '',
          'valid': False
          }

    if not (buf[0] == 0x02 and buf[-1] == 0x03 and len(buf) == 9):
        return d

    temp_units = {0:'C', 2:'K', 3:'F'}
    sensor_types = {0:'K', 1:'J', 2:'E', 3:'T', 4:'R', 5:'S', 6:'N' }

    d['t1'] = (buf[2] * 0xff + buf[3]) / 10.
    d['t1u'] = temp_units[buf[1]]
    d['t2'] = (buf[5] * 0xff + buf[6]) / 10.
    d['t2u'] = temp_units[buf[4]]
    d['type'] = sensor_types[buf[7]]

    d['valid'] = True

    return d


def decode2(buf, start_dt):
    lst = []

    if not (buf[0] == 0x02 and buf[-1] == 0x03 and ((len(buf) - 2 - 3 - 2) % 7 == 0)):
        return 0, lst

    a = buf[1]
    b = buf[2] * 0xff + buf[3]
    c = buf[4]
    sps = buf[5]

    for i, s in enumerate(range(6, len(buf) - 1, 7)):
        bb = buf[s:s+7]
        bb = b'\x02' + bb + b'\x03'
        lst += [decode(bb, start_dt + datetime.timedelta(seconds=i * sps))]

    return sps, lst


def decode_loop(ser):
    s = 0
    s2 = 0
    buf = []
    while True:
        c = ser.read()
        # There's also .read_until(0x03)
        if c == b'':
            print('Timeout')
            continue

        # print(s, s2, c)

        if s2 == 1:
                ser.write(b'\x41\x41')
                #ser.write(b'\x41')
                ser.flush()
        elif s2 == 2:
                ser.write(b'\x55\x55')
                ser.flush()

        if s == 0 and c[0] == 0x02:
            s = 1
            buf = c
        elif s == 1 and c[0] == 0x03:
            buf += c
            #print(buf)
            #print(buf[0])
            #print('buf_len:', len(buf), s2)
            if len(buf) == 9:
                print(decode(buf))
                if s2 == 0:
                    s2 = 1
            elif len(buf) == 5:
                print(buf)
                s2 = 2
            elif s2 in [1, 2]:
                print(decode2(buf, datetime.datetime.now()))
                s2 = 0

            buf = b''
        elif s == 1:
            buf += c


def main(dev_fn):
    with serial.Serial(dev_fn, 9600, timeout=2) as ser:
        decode_loop(ser)


if __name__ == "__main__":
    main('/dev/ttyUSB0')

