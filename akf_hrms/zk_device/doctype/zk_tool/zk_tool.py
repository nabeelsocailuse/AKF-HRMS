# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import socket
from akf_hrms.zk_device.zk_detail.base import ZK
from frappe.utils import date_diff, add_to_date, getdate

employeeDetail=[]

class ZKTool(Document):
	@frappe.whitelist()
	def validate_filters(self):
		if(not self.company):
			frappe.msgprint("Please select company")
		if(not self.employee_list):
			frappe.msgprint("There's no employees in employee list!", title="Employee List")
			return []
		
	@frappe.whitelist()
	def get_company_details(self):
		doctype = 'ZK IP Detail'
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
		def get_conditions():
			conditions = f" and department='{self.department}'" if(self.department) else ""
			conditions += f" and designation='{self.designation}'" if(self.designation) else ""
			conditions += f" and employee='{self.employee}'" if(self.employee) else ""
			return conditions

		employees = frappe.db.sql(f""" select name, employee_name, attendance_device_id 
						from `tabEmployee` 
						where status in ("Active", "Left") 
							and ifnull(attendance_device_id, "")!=""
							and (ifnull(relieving_date, "")="" || relieving_date >= "{self.from_date}")
							and company = '{self.company}' {get_conditions()}""", as_dict=1)
		
		self.total_employees = len(employees)
		self.set("employee_list", [])
		
		for e in  employees:
			self.append("employee_list", 
				{'employee': e.name, 'employee_name': e.employee_name, 'attendance_device_id': e.attendance_device_id})
		

	@frappe.whitelist()
	def fetch_attendance(self):
		self.validate_filters()
		if (self.device_ip and self.device_port):
			addr_ip = socket.gethostbyname(self.device_ip)
			zk = ZK(str(addr_ip), port=int(self.device_port), timeout=4000000, password=0, force_udp=False, ommit_ping=False)
			
			CONN = None
			device_ids = None
			attendance_records = None
			try:
				CONN = zk.connect()
				if (CONN): 
					device_ids = {d.get("attendance_device_id"): {} for d in self.employee_list}
					date_split = (self.from_date).split("-")
					attendance_records = CONN.get_attendance_json(userIds=device_ids, year=date_split[0], month=date_split[1])
			except Exception as e:
				return {"msg": str(e), "logs": attendance_records, "fetched": 0}
			finally:
				if CONN:
					CONN.disconnect()
					return {"msg": "Attendance Fetched.", "logs": attendance_records, "fetched": 1}
		else:
			return {"msg": "Please select right company and log type to 'Get Attendance'", "fetched": 0, "logs": attendance_records}

	@frappe.whitelist()
	def	mark_attendance(self, employees, logs):
		marked = False
		split_date = (self.from_date).split("-")
		year_month = f"{split_date[0]}-{split_date[1]}"
		for row in employees:
			row = frappe._dict(row)
			employee_log = logs[row.attendance_device_id]
			# logs.pop(row.attendance_device_id)
			if(employee_log):
				
				if(year_month in employee_log):
					mlogs = sorted(employee_log[year_month])
					filtered_dates  = []
					for date in get_dates_list(self.from_date, self.to_date):
						filtered_dates += [log for log in mlogs if(date in log)]
					for flog in sorted(filtered_dates):
						args = frappe._dict({
							"company": self.company,
							"employee": row.employee,
							"device_id": row.attendance_device_id,
							"device_ip": self.device_ip,
							"device_port": "4370",
							"log_type": self.log_type,
							"log_from": "ZK Tool",
							"attendance_date": getdate(flog),
							"log": flog,
						})
						if(frappe.db.exists("Attendance Log", args)):
							pass
						else:
							args.update({"doctype": "Attendance Log"})
							frappe.get_doc(args).insert(ignore_permissions=True)
							marked = True
		return {"marked": marked}
	
def get_dates_list(from_date, to_date):
	days = date_diff(to_date, from_date) + 1
	dates_list = []
	for i in range(days):
		new_date = add_to_date(from_date, days=i)
		dates_list.append(new_date)
	return dates_list


@frappe.whitelist()
def activate_live_attendance_service():
	try:
		service_list = ["ksm_live_in.service", "ksm_live_out.service"]
		for sn in service_list:
			command = ["sudo", "systemctl", "status", sn]
			import subprocess, os
			"""
			Run a shell command and capture the output.

			:param command: Command to run as a list (e.g., ['sudo', 'systemctl', 'start', 'service_name'])
			:return: output from the command
			"""
			# Step 1: Change to the directory
			os.chdir('/lib/systemd/system/')
			print("Changed directory to /lib/systemd/system/")
			# Run the command
			output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			# Print the output
			print("Command Output:", output.stdout)
			return output.stdout

	except subprocess.CalledProcessError as e:
		# If there is an error, print the error message
		print("Error:", e.stderr)
		return e.stderr


@frappe.whitelist(allow_guest=True)
def activate_live_attendance_service():
	import subprocess, os
	try:
		service_list = ["live_akfp.service"]
		for sn in service_list:
			command = ["echo", "Z0ng4G?2023"," | ", "sudo -S", "systemctl", "restart", sn]
			
			"""
			Run a shell command and capture the output.

			:param command: Command to run as a list (e.g., ['sudo', 'systemctl', 'restart', 'service_name'])
			:return: output from the command
			"""
			# Step 1: Change to the directory
			os.chdir('/lib/systemd/system/')
			print("Changed directory to /lib/systemd/system/")
			# Run the command
			output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			# Print the output
			print("Command Output:", output.stdout)
			frappe.msgprint(f"{output.stdout}")
		# return output.stdout

	except subprocess.CalledProcessError as e:
		# If there is an error, print the error message
		print("Error:", e.stderr)
		return e.stderr