
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime

@frappe.whitelist(allow_guest=True)
def create_attendance_log(**kwargs):
	kwargs = frappe._dict(kwargs)
	_insert_attedance_log(kwargs)

def _insert_attedance_log(kwargs):
	try:
		frappe.get_doc({
			"doctype": "Attendance Log",
			"device_id": kwargs['device_id'],
			"device_ip": kwargs["device_ip"],
			"device_port": kwargs["device_port"],
			"attendance_date": getdate(kwargs['attendance_date']),
			"log": get_datetime(kwargs['log'])
		}).save(ignore_permissions=True)
		# frappe.db.commit()
	except Exception as e:
		return e




""" from __future__ import unicode_literals
import frappe
from frappe import _
import traceback
import sys
from frappe.utils import getdate

@frappe.whitelist(allow_guest=True)
def create_attendance(**kwargs):
	kwargs = frappe._dict(kwargs)
	# api information
	args = {
		'device_id': kwargs['device_id'],
		'device_ip': kwargs['device_ip'], 
		'device_port': kwargs['device_port'],
		'attendance_date': kwargs['attendance_date'],
		'log': kwargs['log'],
		'doctype': 'Attendance Log'
	}
	frappe.get_doc(args).insert() """

def changePath():
	import subprocess, os, json
	os.chdir('/home/ubuntu/frappe-alkhidmat/')
	print("Changed directory to /lib/systemd/system/")
	 # Define the args as a dictionary
	args = {'id': 1, 'name': 'nabeel'}

	# Convert args to JSON string
	args_json = json.dumps(args)
 
	command = ["bench", "--site", "erp.alkhidmat.org", 
			"execute", "akf_hrms.services.live_capture.biometric_attendance.create_akfp.checkParams",
			"--kwargs", args_json  # Use --kwargs to pass JSON-formatted arguments
			]
	# Run the command
	output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	# Print the output
	print("Command Output:", output.stdout)

def checkParams(**kwargs):
    print(type(kwargs))


# bench --site erp.alkhidmat.org execute akf_hrms.services.live_capture.biometric_attendance.create_akfp.test_jobs_in_background