# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import socket
from akf_hrms.zk_device.zk_detail.base import ZK
from frappe.utils import date_diff, add_to_date, get_datetime

employeeDetail=[]

class ZKTool(Document):
	@frappe.whitelist()
	def get_company_details(self):
		doctype = 'ZK Company Device Detail'
		filters = {'enable': 1, 'company': self.company, 'log_type': self.log_type}
		fieldname = ['*']
		# SQL
		device_detail = frappe.db.get_value(doctype, filters, fieldname, as_dict=1)
		# Set values
		self.device_ip = device_detail.device_ip if(device_detail) else ""
		self.device_port = device_detail.device_port if(device_detail) else ""	
		return device_detail
	
	@frappe.whitelist()
	def get_employees(self):
		# sql for Attendance Device ID
		employeeDetail = frappe.db.sql(""" select 
			attendance_device_id, (name) as employee, 
			ifnull(case when ifnull(default_shift,"")!="" then default_shift else (select shift_type from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date desc limit 1) end, "") as default_shift
		from 
			`tabEmployee` e
		where
			status = 'Active' 
			and ifnull(attendance_device_id, '')!=''
			and company = '%s' 
		group by
			attendance_device_id
		"""%self.company, as_dict=1)
		
		if(employeeDetail): 
			self.employee_detail = str(employeeDetail)
			self.save()
			return "Employees fetched."
		return "Employees not found."
		
	@frappe.whitelist()
	def fetch_attendance(self):
		if (not self.employee_detail): frappe.throw("Please fetch employees first.")

		device_ip = self.device_ip
		device_port = self.device_port
		if (device_ip and device_port):
			conn = None
			addr_ip = socket.gethostbyname(device_ip)
			zk = ZK(str(addr_ip), port=int(device_port), timeout=3000000, password=0, force_udp=False, ommit_ping=False)
			try:
				conn = zk.connect()
				if (conn):
					
					# Dictionary of Attendance Device ID
					userIds = {d.get("attendance_device_id"): {} for d in eval(self.employee_detail) if(d.get("attendance_device_id"))}
					# Fetch from machine
					attendance_records = conn.get_attendance_json(userIds=userIds)
					self.logs_json = str(attendance_records)
					self.save()
					
			except Exception as e:
				return e
			finally:
				if conn:
					conn.disconnect()
					return "Attendance fetched." if(attendance_records) else "Attendance not found."		
		else:
			return "Please select right company and log type to 'Get Attendance' "

	@frappe.whitelist()
	def	mark_attendance(self):
		if(not self.logs_json): 
			frappe.msgprint('Please fetch attendance first!') 
			return
		no_of_days = date_diff(self.to_date, self.from_date) + 1
		if(no_of_days > 10):
			frappe.enqueue('akf_hrms.zk_device.doctype.zk_tool.zk_tool.marking_attendance', self=self, timeout=1000000, queue="long")
			self.progress_message = 'Marking attendance in background.'
			self.save()
		else:
			self.progress_message = 'Marking attendance...'
			# self.save()
			# self.reload()
			return marking_attendance(self)

	@frappe.whitelist()
	def	get_employee_details(self):
		return eval(self.employee_detail) if(self.employee_detail!="None") else []
	
	@frappe.whitelist()
	def get_log_details(self):
<<<<<<< HEAD
		return eval(self.logs_json) if(self.logs_json=="None") else []
	
=======
		return eval(self.logs_json) if(self.logs_json!="None") else []
>>>>>>> f77cdc2 (zk tool condition changes revised.)

@frappe.whitelist()
def marking_attendance(self):
	MARKED = False
	try:
		employee_detail = eval(self.employee_detail)
		logs = eval(self.logs_json)
		dates_list = get_dates_list(self.from_date, self.to_date)
		
		for d in employee_detail:
			multi_years= logs[d.get("attendance_device_id")] if(d.get("attendance_device_id") in logs) else None
			if(multi_years): 
				for date in dates_list:
					year = str(date).split('-')[0]
					signle_year = multi_years[year] if (year in multi_years) else []
					signle_year = sorted(list(signle_year))
					for log in signle_year:
						if (date in log):
							
							attendance_date = str(log).split(" ")[0]
							_log_ = get_datetime(log)
							default_shift = d.get("default_shift")
							# shift = default_shift if (default_shift or default_shift!="") else fetch_shift(self.company, d.get("employee"), log) 
							
							args = {
								'doctype': 'Attendance Log',
								'employee': d.get("employee"),
								'device_id': d.get("attendance_device_id"),
								'shift': default_shift,
								'device_ip': self.device_ip,
								'device_port': self.device_port,
								'log_type': self.log_type,
								'attendance_date': attendance_date,
								'log': _log_,
							}
							
							if(not frappe.db.exists(args)):
								frappe.get_doc(args).save()
								MARKED = True
	except Exception as e:
		return '%s'%e
	finally:
		doc = frappe.get_doc("ZK Tool")
		doc.progress_message = "Attendance marked successfully." if(MARKED) else "Attendance is already marked."
		doc.save()
		doc.reload()

def get_dates_list(from_date, to_date):
	days = date_diff(to_date, from_date) + 1
	dates_list = []
	for i in range(days):
		new_date = add_to_date(from_date, days=i)
		dates_list.append(new_date)
	return dates_list

def fetch_shift(company, employee, log):
	
	shift_assignment = frappe.db.sql(""" 
			select shift_type
			from `tabShift Assignment`
			where docstatus=1
				and status="Active"
				and company='{0}'
				and employee = '{1}'
				-- and cast('{2}' as date) between start_date and end_date
			order by
				start_date desc
			""".format(company, employee, log))
	
	return shift_assignment[0][0] if(shift_assignment) else None

@frappe.whitelist()
def get_sorted_list(unordered_list):
	import ast
	return sorted(ast.literal_eval(unordered_list))

@frappe.whitelist()
def remove_records():
	frappe.db.sql("delete from `tabAttendance`  ")
	frappe.db.sql("delete from `tabAttendance Log`")
