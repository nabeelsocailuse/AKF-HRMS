# This module is overridden by Mubashir on 29-01-2025

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import format_duration, get_link_to_form, time_diff_in_seconds


class JobRequisition(Document):
	def validate(self):
		self.validate_duplicates()
		self.set_time_to_fill()

	def validate_duplicates(self):
		duplicate = frappe.db.exists(
			"Job Requisition",
			{
				"designation": self.designation,
				"department": self.department,
				"requested_by": self.requested_by,
				"status": ("not in", ["Cancelled", "Filled"]),
				"name": ("!=", self.name),
			},
		)

		if duplicate:
			frappe.throw(
				_("A Job Requisition for {0} requested by {1} already exists: {2}").format(
					frappe.bold(self.designation),
					frappe.bold(self.requested_by),
					get_link_to_form("Job Requisition", duplicate),
				),
				title=_("Duplicate Job Requisition"),
			)

	def set_time_to_fill(self):
		if self.status == "Filled" and self.completed_on:
			self.time_to_fill = time_diff_in_seconds(self.completed_on, self.posting_date)

	@frappe.whitelist()
	def associate_job_opening(self, job_opening):
		frappe.db.set_value(
			"Job Opening", job_opening, {"job_requisition": self.name, "vacancies": self.no_of_positions}
		)
		frappe.msgprint(
			_("Job Requisition {0} has been associated with Job Opening {1}").format(
				frappe.bold(self.name), get_link_to_form("Job Opening", job_opening)
			),
			title=_("Job Opening Associated"),
		)


@frappe.whitelist()
def make_job_opening(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.job_title = source.designation
		target.status = "Open"
		target.currency = frappe.db.get_value("Company", source.company, "default_currency")
		target.lower_range = source.expected_compensation
		target.description = source.description

	return get_mapped_doc(
		"Job Requisition",
		source_name,
		{
			"Job Requisition": {
				"doctype": "Job Opening",
			},
			"field_map": {
				"designation": "designation",
				"name": "job_requisition",
				"department": "department",
				"no_of_positions": "vacancies",
			},
		},
		target_doc,
		set_missing_values,
	)


@frappe.whitelist()
def get_avg_time_to_fill(company=None, department=None, designation=None):
	filters = {"status": "Filled"}
	if company:
		filters["company"] = company
	if department:
		filters["department"] = department
	if designation:
		filters["designation"] = designation

	avg_time_to_fill = frappe.db.get_all(
		"Job Requisition",
		filters=filters,
		fields=["avg(time_to_fill) as average_time"],
	)[0].average_time

	return format_duration(avg_time_to_fill) if avg_time_to_fill else 0


# Mubashir Bashir 28-02-2025 Start
@frappe.whitelist()
def get_vacancies_from_staffing_plan(company, branch, department, designation, posting_date):
    staffing_plan = frappe.db.sql("""
        SELECT sp.name, spd.vacancies, spd.current_count
        FROM `tabStaffing Plan` sp
        JOIN `tabStaffing Plan Detail` spd ON sp.name = spd.parent
        WHERE sp.company = %s
		AND sp.department = %s
        AND spd.designation = %s
        AND spd.branch = %s
        AND %s BETWEEN sp.from_date AND sp.to_date
        LIMIT 1
    """, (company, department, designation, branch, posting_date), as_dict=True)

    if staffing_plan:
        staffing_plan_name = staffing_plan[0].name
        total_vacancies = staffing_plan[0].vacancies
        current_count = staffing_plan[0].current_count or 0

        # Calculate already assigned positions
        assigned_positions = frappe.db.sql("""
            SELECT SUM(no_of_positions) as used_positions
            FROM `tabJob Requisition`
            WHERE staffing_plan = %s AND designation = %s AND department = %s AND custom_branch = %s AND docstatus < 2
        """, (staffing_plan_name, designation, department, branch), as_dict=True)

        used_positions = assigned_positions[0].used_positions or 0
        remaining_vacancies = max(total_vacancies - used_positions, 0)

        return {
            "staffing_plan": staffing_plan_name,
            "remaining_vacancies": remaining_vacancies,
            "current_count": current_count
        }
    return None
# Mubashir Bashir 28-02-2025 End