# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff, getdate, get_datetime, time_diff_in_hours, get_time, datetime
from datetime import datetime	# Mubashir Bashir 25-02-2025

class AttendanceLog(Document):
	def validate(self):
		self.set_employee_and_shift_type()

		if(not self.attendance_date):	# Mubashir Bashir 30-07-2025
			frappe.throw("Attendance date and time is required.")

	def set_employee_and_shift_type(self):
		if(self.shift): 
			return
		query = f""" 
				select 
					e.name,
					(Select shift_type from `tabShift Assignment` where docstatus=1 and status="Active" and employee=e.name order by start_date limit 1) as shift_type
				from `tabEmployee` e inner join `tabZK IP Detail` zk on (e.company=zk.company)
				where attendance_device_id='{self.device_id}' and zk.device_ip = '{self.device_ip}'
				group by e.attendance_device_id
				"""
		for d in frappe.db.sql(query, as_dict=1):
			self.employee = d.name
			self.shift = d.shift_type
			
	def after_insert(self):
		self.process_attendance()

	def process_attendance(self):
		attendance = self.get_attendance()
		
		if (attendance):
			self.update_attendance(attendance)
		else:
			self.create_attendance()

	def get_attendance(self):
		return frappe.db.get_value("Attendance", 
				{	
					"docstatus": 1,
					"employee": self.employee,
					"attendance_date": self.attendance_date,
					
				}, ["name", "in_time", "status", "out_time", "custom_in_times", "custom_out_times"], as_dict=1)

	def update_attendance(self, attendance):
		
		if(attendance.status!="Present"): return
		if not attendance.custom_in_times and attendance.custom_out_times:
			frappe.db.set_value("Attendance", attendance.name, "in_time", attendance.out_time)
			frappe.db.set_value("Attendance", attendance.name, "out_time", self.log)
			frappe.db.set_value("Attendance", attendance.name, "custom_in_times", attendance.custom_out_times)
			frappe.db.set_value("Attendance", attendance.name, "custom_out_times", get_time(self.log))
		else:
			frappe.db.set_value("Attendance", attendance.name, "out_time", self.log)
			frappe.db.set_value("Attendance", attendance.name, "custom_out_times", get_time(self.log))
			
		hours_worked = self.cal_hours_worked(attendance.in_time)
		
		frappe.db.set_value("Attendance", attendance.name, "custom_hours_worked", hours_worked)
		frappe.db.set_value("Attendance", attendance.name, "custom_overtime_hours", self.cal_overtime_hours(hours_worked))
		frappe.db.set_value("Attendance", attendance.name, "early_exit", self.early_exit())
	
	def cal_hours_worked(self, in_time):
		# frappe.msgprint(f"{self.log} {in_time}")
		return time_diff(str(self.log), str(in_time))

	# Mubashir Bashir 25-02-2025 Start 
	def create_attendance(self):
		today = datetime.today()
		log_time = datetime.combine(today, get_time(self.log))

		late_entry = False
		early_exit = False
		custom_out_times = ""
		custom_in_times = ""

		if self.shift:

			shift_details = frappe.get_value("Shift Type", self.shift, ["start_time", "end_time"], as_dict=True)
			if not shift_details:
				frappe.throw("Shift details not found for the selected shift.")

			shift_start = datetime.combine(today, get_time(shift_details.get("start_time")))
			shift_end = datetime.combine(today, get_time(shift_details.get("end_time")))
			mid_shift = shift_start + (shift_end - shift_start) / 2			
			
			if log_time <= mid_shift:
				custom_in_times = log_time				
				late_entry = self.late_entry()
			else:				
				custom_out_times = log_time
				early_exit = self.early_exit()
		else:
			custom_in_times = log_time
			
		args = {
			"doctype": "Attendance",
			"employee": self.employee,
			"attendance_date": self.attendance_date,
			"status": "Present",
			"shift": self.shift,
			"in_time": self.log,
			"custom_in_times": custom_in_times,
			"custom_out_times": custom_out_times,
			"late_entry": late_entry,
			"early_exit": early_exit,
		}

		doc = frappe.get_doc(args).save(ignore_permissions=True)
		doc.submit()
		# Mubashir Bashir 25-02-2025 End

	def late_entry(self):
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		log = get_datetime(self.log)
		late_time = log
		if(doc.enable_auto_attendance and doc.custom_grace_in_time): 
			late_time = get_datetime("%s %s"%(getdate(self.log), doc.custom_grace_in_time))
		else:
			late_time = get_datetime("%s %s"%(getdate(self.log), doc.start_time))
		if(log>late_time):
			return True
		else:
			return False

	def early_exit(self):
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		log = get_datetime(self.log)
		exit_time = log
		if(doc.enable_auto_attendance and doc.custom_grace_out_time): 	
			exit_time = get_datetime("%s %s"%(getdate(self.log), doc.custom_grace_out_time))
		else:
			exit_time = get_datetime("%s %s"%(getdate(self.log), doc.end_time))
		
		if(log<exit_time):
			return True
		else:
			return False

	def get_2_hours_late(self):
		if(not self.shift): return False
		doc = frappe.get_doc("Shift Type", self.shift)
		log_in_time = get_datetime(self.log)
		shift_in_time = log_in_time
		if(doc.enable_auto_attendance and doc.custom_grace_in_time): 
			shift_in_time = get_datetime("%s %s"%(getdate(self.log), doc.custom_grace_in_time))
		else:
			shift_in_time = get_datetime("%s %s"%(getdate(self.log), doc.start_time))
		
		hours_differnce = time_diff_in_hours(log_in_time, shift_in_time)
		if(hours_differnce>2):
			return True
		else:
			return False

	def cal_overtime_hours(self, hours_worked):
		overtime_hours = None
		if(not self.shift): 
			return overtime_hours
		total_working_hours = frappe.db.get_value("Shift Type", self.shift, "custom_total_working_hours")
		if(not total_working_hours): 
			return overtime_hours
		if(hours_worked>total_working_hours):
			overtime_hours = time_diff(str(hours_worked), str(total_working_hours))

		return overtime_hours



@frappe.whitelist()
def get_logs_details(filters=None):
	return frappe.db.sql("""
		select device_ip, log_type, log
		from `tabAttendance Log`
		where
			docstatus=0
			and company=%(company)s
			and employee=%(employee)s
			and attendance_date=%(attendance_date)s
	""", filters, as_dict=1)


# Mubashir 25-02-2025 Start

from frappe.utils import nowdate, now_datetime

@frappe.whitelist()
def get_employee_shift(employee):
    """Get latest shift assignment for an employee."""
    shift = frappe.db.sql("""
        SELECT shift_type FROM `tabShift Assignment`
        WHERE employee=%s AND docstatus=1
        ORDER BY start_date DESC LIMIT 1
    """, (employee,), as_dict=True)
    
    return shift[0]['shift_type'] if shift else None

@frappe.whitelist()
def check_attendance_status(employee, shift):
    """Check if the employee already has an attendance log for the same shift today."""
    existing_log = frappe.db.exists("Attendance Log", {
        "employee": employee,
        "shift": shift,
        "attendance_date": nowdate()
    })

    return "check_out" if existing_log else "check_in"

@frappe.whitelist()
def get_current_datetime():
    """Return current date and datetime"""
    return {"date": nowdate(), "datetime": now_datetime()}

@frappe.whitelist()
def record_attendance(docname, button_type, latitude=None, longitude=None):
    """Mark check-in or check-out and update attendance log."""
    doc = frappe.get_doc("Attendance Log", docname)
    
    if button_type in ["mark_check_in", "mark_check_out"]:
        doc.attendance_date = nowdate()
        doc.log = now_datetime()
        if latitude and longitude:
            doc.latitude = latitude
            doc.longitude = longitude

    doc.save()
    return f"{button_type.replace('_', ' ').title()} recorded successfully."

# Mubashir 25-02-2025 Start