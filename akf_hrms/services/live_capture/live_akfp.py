# service path /usr/lib/systemd/system/itc_logistics_in.service
from zk import ZK
# Vriables
conn = None
device_ip = "10.0.7.200"
device_port=4370
company = 'Alkhidmat Foundation Pakistan'
# #########
myobj = {
    "device_id": "51",
    "device_ip": device_ip, 
    "device_port": device_port,
    "attendance_date": "2024-05-24",
    "log": "2024-05-24" + " " + "12:01:00"
}
import requests
url = 'http://erp.alkhidmat.org/api/method/akf_hrms.services.live_capture.biometric_attendance.create_akfp.create_attendance_log'
print("url: ", url)
x = requests.post(url, myobj)
print("post: ", x)
# create ZK instance
# zk = ZK(device_ip, port=device_port, timeout=5000, password=0, force_udp=False, ommit_ping=False)
# try:
#     # print('trying to connect...')
#     # connect to device
#     conn = zk.connect()
#     # disable device, this method ensures no activity on the device while the process is run

#     # conn.disable_device()
#     # another commands will be here!
#     # Example: Get All Users
#     # print(conn)
#     for attendance in conn.live_capture():
#         if attendance is None:
#             print("empty")
#         else:
#             print (attendance) # Attendance object
#             attendanceSplit = str(attendance).split()
#             device_id = attendanceSplit[1]
#             device_date = str(attendanceSplit[3])
#             device_time = str(attendanceSplit[4])
#             myobj = {
#                 "device_id": device_id,
#                 "device_ip": device_ip, 
#                 "device_port": device_port,
#                 "attendance_date": device_date,
#                 "log": device_date + " " + device_time
#             }
#             print(myobj)
#             import requests
#             url = 'http://erp.alkhidmat.org/api/method/akf_hrms.services.live_capture.biometric_attendance.create_akfp.create_attendance_log'
#             print("url: ", url)
#             x = requests.post(url, data = myobj)
#             print("post: ", x)
# except Exception as e:
# 	print ("Process terminate : {}".format(e))
# finally:
# 	if conn:
# 		conn.disconnect()