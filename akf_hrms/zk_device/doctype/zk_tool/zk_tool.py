# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import socket
from akf_hrms.zk_device.zk_detail.base import ZK
from frappe.utils import date_diff, add_to_date, get_datetime, getdate

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
		employeeDetail = frappe.db.get_list('Employee', 
						filters={'status': 'Active', 'company': self.company}, 
						fields=['attendance_device_id', '(name) as employee', 'default_shift'], 
						group_by='attendance_device_id')
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
		if(no_of_days > 5):
			frappe.enqueue('frappe.integrations.doctype.companies_biometrics.companies_biometrics.marking_attendance', self=self, timeout=1000000, queue="long", ignore_links=False, ignore_mandatory=False)
			self.set('progress_message', 'Attendance marking running in background.')
			self.reload()
		else:
			return marking_attendance(self)

@frappe.whitelist()
def marking_attendance(self, ignore_links=False, ignore_mandatory=False):
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
					# signle_year = list(signle_year).sort()
					for log in signle_year:
						if (date in log):
							
							attendance_date = str(log).split(" ")[0]
							frappe.msgprint(f"{attendance_date}")
							
							_log_ = get_datetime(log)
							# frappe.throw(f"{_log_}")
							args = {
								'doctype': 'Attendance Log',
								'employee': d.get("employee"),
								'device_id': d.get("attendance_device_id"),
								'shift': d.get("default_shift"),
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
		# return e
		self.set('progress_message', '%s'%e)
		self.reload()
	finally:
		if(MARKED):
			# return 'Attendance marked successfully.'
			self.set('progress_message', 'Attendance marked successfully.')
		else:
			self.set('progress_message', 'Attendance already marked.')
			# return 'Attendance already marked.'
		# self.reload()

def get_dates_list(from_date, to_date):
	days = date_diff(to_date, from_date) + 1
	dates_list = []
	for i in range(days):
		new_date = add_to_date(from_date, days=i)
		dates_list.append(new_date)
	return dates_list


@frappe.whitelist()
def remove_records():
	frappe.db.sql("delete from `tabAttendance`  ")
	frappe.db.sql("delete from `tabAttendance Log`")