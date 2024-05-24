
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime

@frappe.whitelist(allow_guest=True)
def create_attendance_log(**kwargs):
	kwargs = frappe._dict(kwargs)
	return _insert_attedance_log(kwargs)
	
def get_employee(kwargs):
	query = f""" 
			select 
				e.name,
				(Select name from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date limit 1) as shift_assignment
			from `tabEmployee` e inner join `tabZK IP Detail` zk on (e.company=zk.company)
			where attendance_device_id='{kwargs["device_id"]}' and zk.device_ip = '{kwargs["device_ip"]}'
			group by e.attendance_device_id
			"""
	return frappe.db.sql(query, as_dict=0)

def _insert_attedance_log(kwargs):
	try:
		employee = get_employee(kwargs)
		doc = frappe.new_doc("Attendance Log")
		doc.employee = employee[0][0] if(employee) else None
		doc.device_id = kwargs['device_id']
		doc.device_ip = kwargs["device_ip"]
		doc.device_port = kwargs["device_port"]
		doc.attendance_date = getdate(kwargs['attendance_date'])
		doc.log = get_datetime(kwargs['log'])
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return doc
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