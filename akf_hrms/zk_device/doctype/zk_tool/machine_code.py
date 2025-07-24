from zk import ZK
from datetime import datetime
import time
import os
import logging
 
# Device data
# device_ip = "103.27.22.130"
# device_port = 4370
device_ip = "154.192.53.163"
device_port = 4370  
# Get the directory where this script is located and define the log file path. The file should be at the same directory where the script file is
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "device_log.txt")
 
 
# Configure the logging system to write logs to `device_log.txt`
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
 
#helper function to log message
def log(msg):
    logging.info(msg)
 
# Create the ZK device object with configuration
conn = None
zk = ZK(device_ip, port=device_port, timeout=5, password=0, force_udp=False, ommit_ping=False)
 
# Main loop: keep trying to connect to the device and process attendance
# while True:
try:
    conn = zk.connect()
    log("DEVICE ONLINE")
    attendances = conn.get_attendance()
    # print(attendances)
    for attendance in attendances:
        attendanceSplit = str(attendance).split()
        print(attendanceSplit)
    # for attendance in conn.live_capture():
    #     try:
    #         if attendance:
    #             log(f"ATTENDANCE: {attendance}")
    #     except Exception as e:
    #         log(f"ERROR: {e}")
    #         break

except Exception as e:
    log(f"ERROR: {e}")
    # time.sleep(5)

finally:
    if conn:
        try:
            conn.disconnect()
        except Exception as e:
            log(f"DISCONNECT ERROR: {e}")
    # time.sleep(2) 