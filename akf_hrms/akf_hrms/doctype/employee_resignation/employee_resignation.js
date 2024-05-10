// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Resignation", {
  // refresh: function(frm) {

  // }
  employee: function (frm) {
    frm.set_value("last_working_day", "");
    if (frm.doc.employee) {
      frm.trigger("set_supervisor");
      if (frm.doc.resignation_date && frm.doc.employment_type) {
        frappe.call({
          method:
            "akf_hrms.akf_hrms.doctype.employee_resignation.employee_resignation.get_last_working_day",
          args: {
            resignation_date: frm.doc.resignation_date,
            employment_type: frm.doc.employment_type,
          },
          callback: function (r) {
            if (r.message) {
              frm.set_value("last_working_day", r.message);
            }
          },
        });
      }
    }
  },
  set_supervisor: function (frm) {
    if (frm.doc.employee) {
      // server call is done to include holidays in leave days calculations
      if (frm.doc.company == "Data Support Center") {
        var pc_email = "";
        var emp_branch = String(frm.doc.branch);
        if (emp_branch.match(/Islamabad*/)) {
          pc_email = "islamabaddsc.office@micromerger.com";
        } else if (emp_branch.match(/Karachi*/)) {
          pc_email = "karachi.office@micromerger.com";
        } else if (emp_branch.match(/Quetta*/)) {
          pc_email = "quetta.office@micromerger.com";
        } else if (emp_branch.match(/Peshawar*/)) {
          pc_email = "kpk.office@micromerger.com";
        }
        frm.set_value("supervisor", pc_email);
        frm.set_value("supervisor_name", frappe.user.full_name(pc_email));
      } else {
        return frappe.call({
          method:
            "hrms.hr.doctype.leave_application.leave_application.get_leave_approver",
          args: {
            employee: frm.doc.employee,
          },
          callback: function (r) {
            if (r && r.message) {
              frm.set_value("supervisor", r.message);
              frm.set_value(
                "supervisor_name",
                frappe.user.full_name(frm.doc.supervisor)
              );
            }
          },
        });
      }
    }
  },
  resignation_date: function (frm) {
    if (frm.doc.resignation_date) {
      var resignation_date = Date.parse(frm.doc.resignation_date);
      var today_date = Date.parse(frappe.datetime.nowdate());
      if (resignation_date < today_date) {
        frm.set_value("resignation_date", "");
        frappe.msgprint("Only Future Date Allowed");
      }
    }
    frm.set_value("last_working_day", "");
    if (
      frm.doc.employee &&
      frm.doc.resignation_date &&
      frm.doc.employment_type
    ) {
      frappe.call({
        method:
          "akf_hrms.akf_hrms.doctype.employee_resignation.employee_resignation.get_last_working_day",
        args: {
          resignation_date: frm.doc.resignation_date,
          employment_type: frm.doc.employment_type,
        },
        callback: function (r) {
          if (r.message) {
            frm.set_value("last_working_day", r.message);
          }
        },
      });
    }
  },
});
