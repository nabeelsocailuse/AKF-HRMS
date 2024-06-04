
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
			"doctype": "Proxy Attendance Log",
			"device_id": kwargs['device_id'],
			"device_ip": kwargs["device_ip"],
			"device_port": kwargs["device_port"],
			"attendance_date": getdate(kwargs['attendance_date']),
			"log": get_datetime(kwargs['log'])
		}).insert(ignore_permissions=True)
		frappe.db.commit()
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