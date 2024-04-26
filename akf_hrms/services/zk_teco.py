import frappe
from zk import ZK, const

def get_attendance_zk_teco():
    print('start')
    zk = ZK('103.27.22.130', port=4370, timeout=500, password=0, force_udp=True, ommit_ping=True)
    conn = None
    try:
        print(zk)
        # connect to device
        conn = zk.connect()
        print(conn)
        users = conn.get_users()
        print(users)
    except Exception as e:
        print ("Process terminate : {}".format(e))
    finally:
        if conn:
            conn.disconnect()