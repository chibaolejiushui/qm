import os
import can
import time,datetime
import obuFaw_pb2
import socket
from google.protobuf.internal import encoder, decoder
import pynmea2
import serial
from datetime import datetime

os.system('sudo ip link set can0 type can bitrate 500000')
os.system('sudo ifconfig can0 up')

obumsg = obuFaw_pb2.obuAndCanMotion()


obuudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#SERVER_IP = '192.168.0.103'
#SERVER_IP = '10.133.78.16'
SERVER_IP = '10.133.78.50'
#SERVER_IP = '36.49.91.247'
SERVER_PORT = 8089

obumsg.devID = '964304'
#obumsg.devID = '964317'
SleepTime = 0.2 
speed_old = 0

while True:
    try:
        can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
        msg = can0.recv(0.1)
        if msg is not  None and msg.arbitration_id == 0x10A :
            print(msg)
            mydata = ''
            for i in range(msg.dlc):
                mydata += '{:08b}'.format(msg.data[i])
            print(mydata)
            if mydata[28] == '0' and mydata[29] == '0' :
                obumsg.driveState = 0 
                print(obumsg.driveState)
            elif mydata[28] == '1' and mydata[29] == '0':
                obumsg.driveState = 1 
                print(obumsg.driveState)
            else:
                obumsg.driveState = 3 
                print("else")
        ser = serial.Serial("/dev/ttyS0", baudrate=115200)
        for i in range (3):
            line = ser.readline().decode()
            print(line)
            if line.startswith('$GPGGA'):
                record = pynmea2.parse(line)
                obumsg.longitude = int(float(record.longitude)*10000000)
                obumsg.latitude = int(float(record.latitude)*10000000)
                obumsg.mark1 = int(record.num_sats)
                obumsg.altitude = record.altitude
                if record.gps_qual is 1:
                    obumsg.rtkState = 'A'
                elif record.gps_qual is 4 or 5 :
                    obumsg.rtkState = 'D'
                elif record.gps_qual is 2 :
                    obumsg.rtkState = 'E'
                else :
                    obumsg.rtkState = 'N'
                print(obumsg.longitude,obumsg.latitude,obumsg.mark1,obumsg.altitude,obumsg.rtkState)
            elif line.startswith('$GPVTG'):
                record = pynmea2.parse(line)
                obumsg.speed = record.spd_over_grnd_kmph
                obumsg.accSpeed = (record.spd_over_grnd_kmph - speed_old) / SleepTime
                speed_old = record.spd_over_grnd_kmph
                obumsg.heading = record.true_track
                print(obumsg.speed,obumsg.heading,obumsg.accSpeed)
            elif line.startswith('$GPZDA'):
                record = pynmea2.parse(line)
                timestr =datetime(record.year, record.month , record.day, int(line[7:9]), int(line[9:11]), int(line[11:13]) , int(line[14:16])*10000) 
                timestamp13 = int(timestr.timestamp()*1000) + 28800000
                obumsg.gpsTime = timestamp13
                print(record.timestamp)
                print(timestamp13)
        obumsg_str = obumsg.SerializeToString()
        obumsg_str = encoder._VarintBytes(0x00) + encoder._VarintBytes(0x00) + encoder._VarintBytes(0x10) + encoder._VarintBytes(0x04)+ obumsg_str 
        print (obumsg_str,type(obumsg_str))
        obuudp.sendto(obumsg_str, (SERVER_IP, SERVER_PORT))
        time.sleep(SleepTime)
        print('-------------------------------------------------------------------------------------------------------------')
    except KeyboardInterrupt :
        break
    except :
        continue
   

obuudp.close()
os.system('sudo ifconfig can0 down')
