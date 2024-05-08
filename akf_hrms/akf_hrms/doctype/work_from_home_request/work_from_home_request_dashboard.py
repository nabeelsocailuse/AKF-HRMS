from frappe import _


def get_data():
	return {
		"fieldname": "work_from_home_request",
		"transactions": [
			{"label": _("Atten"), "items": ["Attendance Request"]},
		],
	}
