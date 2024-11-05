
// frappe.ui.form.on("Attendance Request", {
//     refresh(frm) {
//       frm.trigger("show_attendance_warnings");
//     },
  
//     show_attendance_warnings(frm) {
//       if (!frm.is_new() && frm.doc.docstatus === 0) {
//         frm.dashboard.clear_headline();
  
//         frm.call("get_attendance_warnings").then((r) => {
//           if (r.message?.length) {
//             frm.dashboard.reset();
//             frm.dashboard.add_section(
//               frappe.render_template("attendance_warnings", {
//                 warnings: r.message || [],
//               }),
//               __("Attendance Warnings")
//             );
//             frm.dashboard.show();
//           }
//         });
//       }
//     },
  
//     half_day: function (frm) {
//       if (frm.doc.half_day == 1) {
//         frm.set_df_property("half_day_date", "reqd", true);
//       } else {
//         frm.set_df_property("half_day_date", "reqd", false);
//       }
//     },
//     from_date: function (frm) {
//       frm.set_value("to_date", frm.doc.from_date);
//     },
//     employee: function (frm) {
//       if (frm.doc.employee) {
//         frm.trigger("set_leave_approver");
//       }
//     },
//     onload: function (frm) {

//       // Bellow code added by Mubashir

//       if (frappe.user.has_role("Employee")) {
//         frappe.call({
//             method: "frappe.client.get_value",
//             args: {
//                 doctype: "Employee",
//                 fieldname: "name",  
//                 filters: { user_id: frappe.session.user } 
//             },
//             callback: function(response) {
//                 if (response && response.message) {
//                     const employee_id = response.message.name;

//                     frm.set_value("employee", employee_id);
//                     console.log("Employee field populated with ID:", employee_id);
//                 } else {
//                     console.log("No employee found for the current user.");
//                 }
//             }
//         });
//       }

//       // above code added by Mubashir

//       // Set query for employee field based on department
//       frm.set_query("employee", function () {
//         return {
//           filters: {
//             department: frm.doc.department,
//           },
//         };
//       });
//       frm.set_query("work_from_home_request", function () {
//         return {
//           filters: {
//             employee: frm.doc.employee,
//             docstatus: 1,
//           },
//         };
//       });
//     },

//     set_leave_approver: function (frm) {
//       if (frm.doc.employee) {
//         // server call is done to include holidays in leave days calculations
//         return frappe.call({
//           method:
//             "hrms.hr.doctype.leave_application.leave_application.get_leave_approver",
//           args: {
//             employee: frm.doc.employee,
//           },
//           callback: function (r) {
//             if (r && r.message) {
//               frm.set_value("approver", r.message);
//             }
//           },
//         });
//       }
//     },
  
//     approver: function (frm) {
//       if (frm.doc.approver) {
//         frm.set_value("approver_name", frappe.user.full_name(frm.doc.approver));
//       }
//     },
//   });



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
        if (frappe.user.has_role("Employee")) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    fieldname: "name",  
                    filters: { user_id: frappe.session.user } 
                },
                callback: function(response) {
                    if (response && response.message) {
                        const employee_id = response.message.name;
                        frm.set_value("employee", employee_id);
                        console.log("Employee field populated with ID:", employee_id);
                        
                        // After setting employee, check for shift assignment
                        frm.trigger("check_shift_assignment");
                    } else {
                        console.log("No employee found for the current user.");
                    }
                }
            });
        }

        // Set query for employee field based on department
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

    check_shift_assignment: function (frm) {
        if (frm.doc.employee) {
            // Log the employee ID to ensure it's correct
            console.log("Checking shift assignment for employee:", frm.doc.employee);
            
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Shift Assignment", 
                    fields: ["name", "shift_type"], 
                    filters: {
                        employee: frm.doc.employee,
                        docstatus: 1 
                    }
                },
                callback: function(response) {
                    console.log("Shift assignment response:", response); 

                    if (response && response.message && response.message.length > 0) {
                        const shift_type = response.message[0].shift_type; 
                        frm.set_value("shift", shift_type); 
                        console.log("Shift field populated with:", shift_type);
                    } else {
                        console.log("No active shift assignment found for the employee.");
                    }
                }
            });
        }
    },


    set_leave_approver: function (frm) {
        if (frm.doc.employee) {
            // Server call to include holidays in leave days calculations
            return frappe.call({
                method: "hrms.hr.doctype.leave_application.leave_application.get_leave_approver",
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


function loadOpenStreetMap(){
	console.log(navigator.geolocation);
	// if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(openStreetMapFunc);
	// }
}

function openStreetMapFunc(position) {
	console.log(cur_frm.doc.latitude, cur_frm.doc.longitude);
	if (cur_frm.doc.latitude == undefined && cur_frm.doc.longitude == undefined){
		// set current coordinates
		cur_frm.set_value("latitude", position.coords.latitude);
		cur_frm.set_value("longitude", position.coords.longitude);
	}

	latitude =  cur_frm.doc.latitude
	longitude =  cur_frm.doc.longitude
	// latitude = -33.865143
	// longitude = 151.209900
	
	var curLocation = [latitude, longitude];
	
	$("#map_id").empty();
	$("#var_map").html(`<div id="map_id" style="height:400px"></div>`);
	
	setTimeout(() => {
		// if(map != undefined || map != null){
		// 	map.remove();
		//    $("#map").html("");
		// }
		map = window.L.map('map_id').setView(curLocation, 16);
		
		const tiles = window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
			maxZoom: 19,
			attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
		}).addTo(map);

		const marker = window.L.marker(curLocation).addTo(map);
		// .bindPopup('<b>Hello world!</b><br />I am a popup.').openPopup();
		
		map.panTo(new window.L.LatLng(latitude, longitude));

	}, 500);
}