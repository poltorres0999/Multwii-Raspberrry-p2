import time
import serial
import struct

import Drone
import MultiwiiSettings


class MultiWii(object):

    # Multiwii Serial Protocol message IDs.
    # Getters
    IDENT = 100
    STATUS = 101
    RAW_IMU = 102
    SERVO = 103
    MOTOR = 104
    RC = 105
    RAW_GPS = 106
    COMP_GPS = 107
    ATTITUDE = 108
    ALTITUDE = 109
    ANALOG = 110
    RC_TUNING = 111
    PID = 112
    BOX = 113
    MISC = 114
    MOTOR_PINS = 115
    BOXNAMES = 116
    PIDNAMES = 117
    WP = 118
    BOXIDS = 119
    RC_RAW_IMU = 121

    # Setters
    SET_RAW_RC = 200
    SET_RAW_GPS = 201
    SET_PID = 202
    SET_BOX = 203
    SET_RC_TUNING = 204
    ACC_CALIBRATION = 205
    MAG_CALIBRATION = 206
    SET_MISC = 207
    RESET_CONF = 208
    SET_WP = 209
    SWITCH_RC_SERIAL = 210
    IS_SERIAL = 211
    DEBUG = 254

    def __init__(self):

        self.drone = Drone.Drone()

        try:
            self.settings = MultiwiiSettings.Settings()
            self.serial = self.settings.serial_port
            self.serial.open()
            time.sleep(self.settings.wakeup)
        except ValueError as err:
            print('Serial port exception:' + str(err) + '\n')

    def send_cmd(self, data_length, code, data):

        checksum = 0
        total_data = ['$', 'M', '<', data_length, code] + data
        for i in struct.pack('<2B%dH' % len(data), *total_data[3:len(total_data)]):
            checksum = checksum ^ ord(i)
        total_data.append(checksum)
        try:
            b = None
            b = self.serial.write(struct.pack('<3c2B%dHB' % len(data), *total_data))
        except ValueError as err:
            print('Serial port exception:' + str(err) + '\n')

    def get_data(self, cmd):

        try:
            start = time.time()
            self.send_cmd(0, cmd, [])

            header = self.serial.read()
            while header != '$':
                header = self.serial.read()

            preamble = self.serial.read()
            direction = self.serial.read()
            size = struct.unpack('<b', self.serial.read())[0]
            cmd = self.serial.read()
            data = self.serial.read(size)
            total_data = struct.unpack('<' + 'h' * (size / 2), data)

            print total_data

            self.serial.flushInput()
            self.serial.flushOutput()

            elapsed = time.time() - start

            return total_data, elapsed

        except serial.SerialException as err:
            print('Serial port exception:' + str(err) + '\n')

    def arm(self):

        start = time.time()
        while (time.time() - start) < 0.5:
            self.set_rc([1500, 1500, 2000, 1000])

    def disarm(self):
        start = time.time()
        while (time.time() - start) < 0.5:
            self.set_rc([1500, 1500, 1000, 1000])

    def get_altitude(self):

        total_data, elapsed = self.get_data(MultiWii.ALTITUDE)

        print total_data

        self.drone.altitude['estalt'] = float(total_data[0])
        self.drone.altitude['vario'] = float(total_data[1])
        self.drone.altitude['elapsed'] = round(elapsed, 3)
        self.drone.altitude['timestamp'] = "%0.2f" % (time.time(),)

        return self.drone.altitude

    def get_attitude(self):

        total_data, elapsed = self.get_data(MultiWii.ATTITUDE)

        self.drone.attitude['angx'] = float(total_data[0] / 10.0)
        self.drone.attitude['angy'] = float(total_data[1] / 10.0)
        self.drone.attitude['heading'] = float(total_data[2])
        self.drone.attitude['elapsed'] = round(elapsed, 3)
        self.drone.attitude['timestamp'] = "%0.2f" % (time.time(),)

        return self.drone.attitude

    def get_rc(self):

        total_data, elapsed = self.get_data(MultiWii.RC)

        self.drone.rc_channels['roll'] = total_data[0]
        self.drone.rc_channels['pitch'] = total_data[1]
        self.drone.rc_channels['yaw'] = total_data[2]
        self.drone.rc_channels['throttle'] = total_data[3]
        self.drone.rc_channels['elapsed'] = round(elapsed, 3)
        self.drone.rc_channels['timestamp'] = "%0.2f" % (time.time(),)

        return self.drone.rc_channels

    def get_raw_imu(self):

        total_data, elapsed = self.get_data(MultiWii.RAW_IMU)

        self.drone.raw_imu['accx'] = float(total_data[0])
        self.drone.raw_imu['accy'] = float(total_data[1])
        self.drone.raw_imu['accz'] = float(total_data[2])
        self.drone.raw_imu['gyrx'] = float(total_data[3])
        self.drone.raw_imu['gyry'] = float(total_data[4])
        self.drone.raw_imu['gyrz'] = float(total_data[5])
        self.drone.raw_imu['magx'] = float(total_data[6])
        self.drone.raw_imu['magy'] = float(total_data[7])
        self.drone.raw_imu['magz'] = float(total_data[8])
        self.drone.raw_imu['elapsed'] = round(elapsed, 3)
        self.drone.raw_imu['timestamp'] = "%0.2f" % (time.time(),)

        return self.drone.raw_imu

    def get_motor(self):

        total_data, elapsed = self.get_data(MultiWii.MOTOR)

        self.drone.motor['m1'] = float(total_data[0])
        self.drone.motor['m2'] = float(total_data[1])
        self.drone.motor['m3'] = float(total_data[2])
        self.drone.motor['m4'] = float(total_data[3])
        self.drone.motor['elapsed'] = "%0.3f" % (elapsed,)
        self.drone.motor['timestamp'] = "%0.2f" % (time.time(),)

        return self.drone.motor

    def get_servo(self):

        total_data, elapsed = self.get_data(MultiWii.SERVO)

        self.drone.servo['s1'] = float(total_data[0])
        self.drone.servo['s2'] = float(total_data[1])
        self.drone.servo['s3'] = float(total_data[2])
        self.drone.servo['s4'] = float(total_data[3])
        self.drone.servo['elapsed'] = "%0.3f" % (elapsed,)
        self.drone.servo['timestamp'] = "%0.2f" % (time.time(),)

        return self.drone.servo

    def set_rc(self, rc_data):

        self.send_cmd(8, MultiWii.SET_RAW_RC, rc_data)



















