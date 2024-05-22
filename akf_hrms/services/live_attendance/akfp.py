# service path /usr/lib/systemd/system/itc_logistics_in.service

from akf_hrms.zk_device.zk_detail.base import ZK

# Vriables
conn = None
# create ZK instance
zk = ZK("10.0.7.200", port=4370, timeout=5000, password=0, force_udp=True, ommit_ping=True)
try:
    # connect to device
    conn = zk.connect()
    # disable device, this method ensures no activity on the device while the process is run

    # conn.disable_device()
    # another commands will be here!
    # Example: Get All Users

    for attendance in conn.live_capture():
        if attendance is None:
            print("empty")
        else:
            # print (attendance) # Attendance object
            attendanceSplit = str(attendance).split()
            device_id = attendanceSplit[1]
            datee = str(attendanceSplit[3])
            itmee = str(attendanceSplit[4])
            company = 'Alkhidmat Foundation Pakistan'

            import requests
            url = 'http://erp.alkhidmat.org:8023/api/method/akf_hrms.services.live_capture.biometric_attendance.create_akfp.create_attendance'
            myobj = {'idd': device_id, 'log_time': datee + " " + itmee, 'ip_': "192.168.0.195", 'company': company}
            x = requests.post(url, data = myobj)
except Exception as e:
	print ("Process terminate : {}".format(e))
finally:
	if conn:
		conn.disconnect()
