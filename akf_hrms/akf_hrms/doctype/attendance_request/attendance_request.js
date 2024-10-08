
frappe.ui.form.on("Attendance Request", {
    refresh(frm) {
      frm.trigger("show_attendance_warnings");
    },
  
    show_attendance_warnings(frm) {
      if (!frm.is_new() && frm.doc.docstatus === 0) {
        frm.dashboard.clear_headline();
  
        frm.call("get_attendance_warnings").then((r) => {
          if (r.message?.length) {
            frm.dashboard.reset();
            frm.dashboard.add_section(
              frappe.render_template("attendance_warnings", {
                warnings: r.message || [],
              }),
              __("Attendance Warnings")
            );
            frm.dashboard.show();
          }
        });
      }
    },
  
    half_day: function (frm) {
      if (frm.doc.half_day == 1) {
        frm.set_df_property("half_day_date", "reqd", true);
      } else {
        frm.set_df_property("half_day_date", "reqd", false);
      }
    },
    from_date: function (frm) {
      frm.set_value("to_date", frm.doc.from_date);
    },
    employee: function (frm) {
      if (frm.doc.employee) {
        frm.trigger("set_leave_approver");
      }
    },
    onload: function (frm) {
      frm.set_query("employee", function () {
        return {
          filters: {
            department: frm.doc.department,
          },
        };
      });
      frm.set_query("work_from_home_request", function () {
        return {
          filters: {
            employee: frm.doc.employee,
            docstatus: 1,
          },
        };
      });
    },
    set_leave_approver: function (frm) {
      if (frm.doc.employee) {
        // server call is done to include holidays in leave days calculations
        return frappe.call({
          method:
            "hrms.hr.doctype.leave_application.leave_application.get_leave_approver",
          args: {
            employee: frm.doc.employee,
          },
          callback: function (r) {
            if (r && r.message) {
              frm.set_value("approver", r.message);
            }
          },
        });
      }
    },
  
    approver: function (frm) {
      if (frm.doc.approver) {
        frm.set_value("approver_name", frappe.user.full_name(frm.doc.approver));
      }
    },
  });
  