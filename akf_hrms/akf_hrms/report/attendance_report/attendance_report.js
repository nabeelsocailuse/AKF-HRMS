// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

// Mubashir Bashir

frappe.query_reports["Attendance Report"] = {
	"filters": [{
			"label": "Department",
			"fieldtype": "Link",
			"fieldname": "department",
			"options": "Department",
			"reqd": 0,
		},
		{
			"label": "Region",
			"fieldtype": "Link",
			"fieldname": "region",
			"options": "Region",
			"reqd": 0,
		}, 
		{
			"label": "Date",
			"fieldtype": "Date",
			"fieldname": "date",
			"default": frappe.datetime.nowdate("dd-mm-yyyy"),
			"reqd": 0,
		},
		
		{
			"label": "Report Type",
			"fieldtype": "Select",
			"fieldname": "report_type",
			"options": ["Absentees", "Late Arrival", "Early Leavers", "Check In/Out Missing" ,"Pending Attendance Requests", "Pending Leaves", "Approved Leaves", "Pending Comp Off Requests", "Approved Comp Off" ],
			"reqd": 0,
		}	

	]
};
