from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    date_diff,
    add_days,
    getdate,
    get_link_to_form,
    getdate,
    format_date,
    nowdate,
    time_diff,
    get_datetime,
    get_time
)
from erpnext.setup.doctype.employee.employee import is_holiday

from akf_hrms.utils.attendance_request_utils import (
	setting_next_workflow_approver,
	record_workflow_approver_states
)
class OverlappingAttendanceRequestError(frappe.ValidationError):
    pass


class AttendanceRequest(Document):
	# Function overide and Changed
	def validate(self):
		self.validate_travel_dates() # Mubashir Bashir 4-6-25
		self.validate_future_request_and_date_of_joining() # nabeel saleem, 20-12-2024
		# self.mark_check_in_on_save() # nabeel saleem, 20-12-2024
		self.validate_from_time_and_to_time() # nabeel saleem, 20-12-2024
		self.validate_half_day() # nabeel saleem, 20-12-2024
		# self.validate_work_from_home() # Commented by Mubashir on 07-02-2025
		# self.validate_request_overlap() # Mubashir 12-03-2025

		# self.set_next_workflow_state() # Mubashir Bashir 11-03-2025
		# self.set_next_workflow_approver() # Mubashir Bashir 11-03-2025
		# self.record_application_state() # Mubashir Bashir, 11-03-2025	
		""" Nabeel Saleem, 16-05-2025 """
		setting_next_workflow_approver(self)
		record_workflow_approver_states(self)
	
	def on_submit(self):
		self.mark_check_out_on_submit() # nabeel saleem, 20-12-2024
		self.cannot_submit_own_attendance_request() # nabeel saleem, 20-12-2024
		self.create_attendance_records()

	def validate_future_request_and_date_of_joining(self):
		date_of_joining = frappe.db.get_value(
				"Employee", self.employee, "date_of_joining"
			)
		# Attendance can not be marked for future dates
		if getdate(self.from_date) > getdate(nowdate()):
			frappe.throw(
				_("Attendance cannot be requested for future dates: {0}").format(
					frappe.bold(format_date(self.from_date)),
				)
			)
		elif (date_of_joining and getdate(self.from_date) < getdate(date_of_joining)):
			frappe.throw(
				_(
					"Attendance date {0} can not be less than employee {1}'s joining date: {2}"
				).format(
					frappe.bold(format_date(self.from_date)),
					frappe.bold(self.employee),
					frappe.bold(format_date(date_of_joining)),
				)
			)

	def mark_check_in_on_save(self):
		if(self.reason and self.reason not in ["", "Check In/Out Miss"]):
			if (not self.from_time):
				frappe.throw(_("Please mark check in using the 'Mark Check In' button"), title="From Time Required")
			
	
	def mark_check_out_on_submit(self):
		if(self.reason not in ["", "Check In/Out Miss"]):
			if (not self.to_time):
				frappe.throw(_("Please mark check out using the 'Mark Check Out' button"), title="To Time Required")
	
	def validate_from_time_and_to_time(self):
		if(self.reason in ["Check In/Out Miss"]):
			if get_time(self.to_time) < get_time(self.from_time):
				frappe.throw("To-Time cannot be less than From-Time", title=f"{self.reason}")
	
	def validate_half_day(self):
		if (self.half_day):
			if (
				not getdate(self.from_date)
				<= getdate(self.half_day_date)
				<= getdate(self.to_date)
			):
				frappe.throw(
					_("Half day date should be in between from date and to date")
				)

	def validate_work_from_home(self):
		if self.reason == "Work From Home":
			if not self.work_from_home_request:
				frappe.throw(
					_("Mandatory field required <b>Work From Home Request</b>")
				)
			self.check_wfh_days()
		
	def validate_request_overlap(self):
		if not self.name:
			self.name = "New Attendance Request"

		Request = frappe.qb.DocType("Attendance Request")
		overlapping_request = (
			frappe.qb.from_(Request)
			.select(Request.name)
			.where(
				(Request.employee == self.employee)
				& (Request.docstatus < 2)
				& (Request.name != self.name)
				& (self.to_date >= Request.from_date)
				& (self.from_date <= Request.to_date)
				& (self.to_time >= Request.from_time)
				& (self.from_time <= Request.to_time)
			)
		).run(as_dict=True)

		if overlapping_request:
			self.throw_overlap_error(overlapping_request[0].name)

	def throw_overlap_error(self, overlapping_request: str):
		msg = _(
			"Employee {0} already has an Attendance Request {1} that overlaps with this period"
		).format(
			frappe.bold(self.employee),
			get_link_to_form("Attendance Request", overlapping_request),
		)

		frappe.throw(
			msg,
			title=_("Overlapping Attendance Request"),
			exc=OverlappingAttendanceRequestError,
		)
		
	# Mubashir Bashir 4-56-25 Start
	def validate_travel_dates(self):
		if not self.travel_request: return
		query = f"""
					SELECT departure_date, arrival_date
					FROM `tabTravel Itinerary`
					WHERE parent = '{self.travel_request}'
				"""
		result = frappe.db.sql(query, as_dict=1)
		if(result):
			departure_date=getdate(result[0].departure_date)
			arrival_date=getdate(result[0].arrival_date)
		else:
			frappe.throw(f"No date found for travel request: {self.travel_request}")
		if (not departure_date<= getdate(self.from_date) <= arrival_date):
			frappe.throw(_("Attendance Request Date should be between Departure Date and Arrival Date"))
	# Mubashir Bashir 4-56-25 End

	def on_cancel(self):
		attendance_list = frappe.get_all(
			"Attendance",
			{
				"employee": self.employee,
				"attendance_request": self.name,
				"docstatus": 1,
			},
		)
		if attendance_list:
			for attendance in attendance_list:
				attendance_obj = frappe.get_doc("Attendance", attendance["name"])
				attendance_obj.cancel()

	# Custom Function
	def check_wfh_days(self):
		from_date = frappe.db.get_value(
			"Work From Home Request", self.work_from_home_request, "from_date"
		)
		to_date = frappe.db.get_value(
			"Work From Home Request", self.work_from_home_request, "to_date"
		)
		if from_date <= getdate(self.from_date) <= to_date:
			pass
		else:
			frappe.throw(
				"Attendance Request date must be in between {0} and {1}".format(
					from_date, to_date
				)
			)

	def cannot_submit_own_attendance_request(self):
		emp_user_id = frappe.get_value("Employee", self.employee, "user_id")
		if emp_user_id == frappe.session.user:
			frappe.throw("You can not Submit your own Attendance Request!")

	def create_attendance_records(self):
		request_days = date_diff(self.to_date, self.from_date) + 1
		for day in range(request_days):
			attendance_date = add_days(self.from_date, day)
			if self.should_mark_attendance(attendance_date):
				self.create_or_update_attendance(attendance_date)

	def create_or_update_attendance(self, date: str):
		attendance_name = self.get_attendance_record(date)
		status = self.get_attendance_status(date)
		hours_worked = time_diff(self.to_time, self.from_time)
		hours_worked = str(hours_worked.total_seconds() / 3600)	# Added by Mubashir Bashir on 5-3-25
		if("." in hours_worked): hours_worked = hours_worked.split(".")[0]
		# if("." in hours_worked): hours_worked = str(hours_worked)["."][0]
		if attendance_name:
			# update existing attendance, change the status
			doc = frappe.get_doc("Attendance", attendance_name)
			old_date = str(doc.in_time) + " - " + str(doc.out_time)
			f_date = str(self.from_date) + " " + str(self.from_time)
			t_date = str(self.from_date) + " " + str(self.to_time)
			new_date = str(f_date) + " - " + str(t_date)
			doc.db_set(
				{
					"in_time": f_date,
					"out_time": t_date,
					"custom_hours_worked": hours_worked,
					"custom_in_times": self.from_time,
					"custom_out_times": self.to_time
				}
			)
			frappe.msgprint(
				_(
					"Updated In-Out Details from {0} to {1} for date {2} in the attendance record {3}"
				).format(
					frappe.bold(old_date),
					frappe.bold(new_date),
					frappe.bold(format_date(date)),
					get_link_to_form("Attendance", doc.name),
				),
				title=_("Attendance Updated"),
			)
			old_status = doc.status

			if old_status != status:
				doc.db_set({"status": status, "attendance_request": self.name})
				text = _(
					"changed the status from {0} to {1} via Attendance Request"
				).format(frappe.bold(old_status), frappe.bold(status))
				doc.add_comment(comment_type="Info", text=text)

				frappe.msgprint(
					_(
						"Updated status from {0} to {1} for date {2} in the attendance record {3}"
					).format(
						frappe.bold(old_status),
						frappe.bold(status),
						frappe.bold(format_date(date)),
						get_link_to_form("Attendance", doc.name),
					),
					title=_("Attendance Updated"),
				)
			doc.save(ignore_permissions=True)
		else:
			# submit a new attendance record
			doc = frappe.new_doc("Attendance")
			doc.employee = self.employee
			doc.attendance_date = date
			doc.shift = self.shift
			doc.company = self.company
			doc.attendance_request = self.name
			doc.custom_hours_worked = hours_worked
			doc.in_time = str(self.from_date) + " " + str(self.from_time)
			doc.out_time = str(self.from_date) + " " + str(self.to_time)
			doc.custom_in_times = self.from_time
			doc.custom_out_times = self.to_time
			doc.status = status
			doc.insert(ignore_permissions=True)
			doc.submit()

	def should_mark_attendance(self, attendance_date: str) -> bool:
		# Check if attendance_date is a holiday
		if not self.include_holidays and is_holiday(self.employee, attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as it is a Holiday.").format(
					frappe.bold(format_date(attendance_date))
				)
			)
			return False

		# Check if employee is on leave
		if self.has_leave_record(attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as {1} is on leave.").format(
					frappe.bold(format_date(attendance_date)),
					frappe.bold(self.employee),
				)
			)
			return False

		return True

	def has_leave_record(self, attendance_date: str) -> str | None:
		return frappe.db.exists(
			"Leave Application",
			{
				"employee": self.employee,
				"docstatus": 1,
				"from_date": ("<=", attendance_date),
				"to_date": (">=", attendance_date),
			},
		)

	def get_attendance_record(self, attendance_date: str) -> str | None:
		return frappe.db.exists(
			"Attendance",
			{
				"employee": self.employee,
				"attendance_date": attendance_date,
				"docstatus": ("!=", 2),
			},
		)

	def get_attendance_status(self, attendance_date: str) -> str:
		if (
			self.half_day
			and date_diff(getdate(self.half_day_date), getdate(attendance_date)) == 0
		):
			return "Half Day"
		elif self.reason == "Work From Home":
			return "Work From Home"
		else:
			return "Present"

	@frappe.whitelist()
	def get_attendance_warnings(self) -> list:
		attendance_warnings = []
		request_days = date_diff(self.to_date, self.from_date) + 1

		for day in range(request_days):
			attendance_date = add_days(self.from_date, day)

			if not self.include_holidays and is_holiday(self.employee, attendance_date):
				attendance_warnings.append(
					{"date": attendance_date, "reason": "Holiday", "action": "Skip"}
				)
			elif self.has_leave_record(attendance_date):
				attendance_warnings.append(
					{"date": attendance_date, "reason": "On Leave", "action": "Skip"}
				)
			else:
				attendance = self.get_attendance_record(attendance_date)
				if attendance:
					doc = frappe.get_doc("Attendance", attendance)
					attendance_warnings.append(
						{
							"date": attendance_date,
							"reason": "Attendance already marked",
							"record": attendance,
							"action": "Overwrite",
							"in_time": doc.in_time,
							"out_time": doc.out_time,
						}
					)
		return attendance_warnings

	@frappe.whitelist()
	def get_current_time(self):
		cur_time = get_datetime()
		return str(cur_time).split(" ")[1]


	# Mubashir Bashir 11-03-2025 Start
	@frappe.whitelist()
	def set_next_workflow_approver(self):
		if(not hasattr(self, 'workflow_state')): return		
		# if(self.status!='Open'): return

		# => find approver
		def set_approver_detail(user_id):
			self.approver = user_id
			self.approver_name = frappe.utils.get_fullname(user_id)

		if (self.custom_next_workflow_state == 'Recommended by Line Manager'):
			reports_to = frappe.db.get_value('Employee', {'name': self.employee}, 'reports_to')
			if(reports_to):
				user_id = frappe.db.get_value('Employee', {'name': reports_to}, 'user_id')
				if(frappe.db.exists('Has Role', {'parent': user_id, 'role': 'Line Manager'})):
					set_approver_detail(user_id)
			else:
				frappe.throw(f"Please set a `reports to` of this employee", title="Line Manager")
					
		elif(self.custom_next_workflow_state == 'Recommended by Head of Department'):
			user_id = frappe.db.get_value('Employee', {'department': self.department , 'custom_hod': 1}, 'user_id')
			if(user_id):
				set_approver_detail(user_id)
			else:
				frappe.throw(f"Please set a `head of department` of department {self.department}", title="Head of Department")
		
		elif(self.custom_next_workflow_state == 'Approved'):
			user_list = frappe.db.sql(""" 
					Select 
						u.name 
					From 
						`tabUser` u inner join `tabHas Role` h on (u.name=h.parent) 
					Where 
						h.role in ('CEO')
					Group by
						u.name 
			""")
			if(user_list):
				set_approver_detail(user_list[0][0])
			else:
				frappe.throw(f"Please set a `CEO` of {self.company}", title="CEO")

	def set_next_workflow_state(self):
		employee_user_id = frappe.db.get_value("Employee", self.employee, "user_id")

		if not employee_user_id: return

		employee_roles = frappe.get_roles(employee_user_id)

		if (frappe.db.exists('Employee', {'name': self.employee, 'custom_directly_reports_to_hod': 0}) and 
			"Employee" in employee_roles and 
			not any(role in employee_roles for role in ["Line Manager", "Head of Department", "CEO", "Executive Director"])):
			if (self.custom_next_workflow_state == 'Recommended by Line Manager'):
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Line Manager to Head of Department'
			elif (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Line Manager'
				self.custom_workflow_indication = 'Recommended to Line Manager'


		elif (frappe.db.exists('Employee', {'name': self.employee, 'custom_directly_reports_to_hod': 1}) and 
			"Employee" in employee_roles and 
			not any(role in employee_roles for role in ["Line Manager", "Head of Department", "CEO"])):
			if (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Applied to HOD'


		elif "Line Manager" in employee_roles and not any(role in employee_roles for role in ["Head of Department", "CEO", "Executive Director"]):
			if (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Applied to HOD'
				

		elif "Head of Department" in employee_roles and not any(role in employee_roles for role in ["CEO", "Executive Director"]):
			self.custom_next_workflow_state = 'Approved'
			self.custom_workflow_indication = 'Applied to CEO'

	def record_application_state(self):
		if(hasattr(self, 'workflow_state')):
			from frappe.utils import get_datetime
			state_dict = eval(self.custom_state_data) if(self.custom_state_data) else {}
			# if(self.workflow_state not in state_dict):
			state_dict.update({f"{self.workflow_state}": {
				"current_user": f"{self.workflow_state} (<b>{frappe.utils.get_fullname(frappe.session.user)}</b>)",
				"next_state": f"{self.custom_next_workflow_state} (<b>{self.approver_name}</b>)" if "CEO" not in frappe.get_roles(frappe.session.user) and "Executive Director" not in frappe.get_roles(frappe.session.user) else "",
				"modified_on": get_datetime(),
			}})
			self.custom_state_data =  frappe.as_json(state_dict)

	# Mubashir Bashir 11-03-2025 End


# @frappe.whitelist()
# def update_workflow_state():
#     frappe.db.sql("""
#         UPDATE `tabAttendance Request`
#         SET status = 'Approved'
#         WHERE docstatus = 1
#     """)
#     frappe.db.commit()
#     print("status field updated from empty to Open")

