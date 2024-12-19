var latitude = '';
var longitude = '';
var map;

frappe.ui.form.on("Attendance Request", {
    refresh(frm) {
        frm.trigger("show_attendance_warnings");
        frm.trigger("triggerOpenStreetMap");
        if(!frm.doc.__islocal && frm.doc.from_time){
			hide_field(frm, 'mark_check_in')
		}
		if(!frm.doc.__islocal && frm.doc.to_time && frm.doc.mark_check_condition ){
			hide_field(frm, 'mark_check_out')
			show_field(frm, 'to_time')
		}else{
			hide_field(frm, 'to_time')
		}
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
        // start: Mubashir Bashir, 12-11-2024
        if (frm.doc.employee && frm.doc.from_date) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Attendance",
                    fields: ["in_time", "out_time"],
                    filters: {
                        employee: frm.doc.employee,
                        attendance_date: frm.doc.from_date,
                        docstatus: 1 
                    },
                    limit: 1
                },
                callback: function(response) {
                    if (response && response.message && response.message.length > 0) {
                        const attendance = response.message[0];
                        
                        if (attendance.in_time) {
                            const inTime = attendance.in_time.substring(11, 19);
                            frm.set_value("custom_from", inTime);
                        }
                        
                        if (attendance.out_time) {
                            const outTime = attendance.out_time.substring(11, 19); 
                            frm.set_value("custom_to", outTime);
                        }
                    } else {
                        console.log("No attendance record found for the selected date.");
                    }
                }
            });
        }
        // end: Mubashir Bashir, 12-11-2024
    },

    employee: function (frm) {
        if (frm.doc.employee) {
            frm.trigger("set_leave_approver");
            frm.trigger("check_shift_assignment"); // Mubashir Bashir 12-11-2024
        }
    },

    onload: function (frm) {
        frm.trigger('triggerOpenStreetMap');
        if (frappe.user.has_role("Employee") && frm.doc.employee == undefined) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    fieldname: "name",
                    filters: { user_id: frappe.session.user }
                },
                callback: function (response) {
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
                callback: function (response) {
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
    triggerOpenStreetMap: function (frm) {
        if(cur_frm.doc.docstatus == 0){
            CallOpenStreetMap();
        }
        if(cur_frm.doc.docstatus < 2){
            setupOpenStreetMap();
        }
    },
    mark_check_in: function(frm){
		get_current_time(frm, 'from_time','mark_check_in')
	},
	mark_check_out: function(frm){
		get_current_time(frm, 'to_time', 'mark_check_out')
		show_field(frm, 'to_time');
        setTimeout(() => {
            frm.set_value('mark_check_condition', 1);
        }, 100);
		
	},
});


function CallOpenStreetMap() {
    
    if (cur_frm.doc.latitude == undefined || cur_frm.doc.longitude == undefined) {
        navigator.permissions.query({ name: 'geolocation' }).then((result) => {
            console.log(result)
            if (result.state === 'denied') {
                alert("Please enable location access in your browser settings for this feature to work.");
            }
            else if (result.state === 'granted') {
                // Permission is granted, start geolocation tracking
                getLocation();
            }
            else if (result.state === 'prompt') {
                // If permission has not been asked yet, request it
                getLocation();
                // requestLocationPermission();
            }
            else {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        if (cur_frm.doc.latitude == '' && cur_frm.doc.longitude == '') {
                            cur_frm.set_value("latitude", position.coords.latitude);
                            cur_frm.set_value("longitude", position.coords.longitude);
                            return true
                        }
                    },
                    (error) => {
                        console.error("Geolocation error:", error.message);
                    }
                );
            }
        });
    }

}

function getLocation() {
    console.log(navigator.geolocation);
    if (navigator.geolocation) {
        console.log('in: ');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log('position: ');
                cur_frm.set_value("latitude", position.coords.latitude);
                cur_frm.set_value("longitude", position.coords.longitude);
            },
            (error) => {
                console.log('error: ');
                if (error.code === error.PERMISSION_DENIED) {
                    alert("Geolocation permission was revoked. Please re-enable it in your browser settings.");
                } else {
                    console.error("Geolocation error:", error.message);
                }
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

function requestLocationPermission() {
    console.log('requestLocationPermission')
    navigator.geolocation.getCurrentPosition(
        (position) => {
            console.log("Geolocation granted:", position);
            // console.log(pos)
            // Handle successful permission grant
        },
        (error) => {
            if (error.code === error.PERMISSION_DENIED) {
                alert("Geolocation permission denied. Please enable it in your browser settings.");
            }
        }
    );
}

function setupOpenStreetMap() {
    /* if ((cur_frm.doc.latitude == undefined || cur_frm.doc.latitude == "") && (cur_frm.doc.longitude == undefined || cur_frm.doc.longitude == "")){
        // set current coordinates
        cur_frm.set_value("latitude", position.coords.latitude);
        cur_frm.set_value("longitude", position.coords.longitude);
    } */

    if ((cur_frm.doc.latitude == undefined || cur_frm.doc.latitude == "") && (cur_frm.doc.longitude == undefined || cur_frm.doc.longitude == "")) {
        return
    }
    const latitude = cur_frm.doc.latitude;
    const longitude = cur_frm.doc.longitude;
    var curLocation = [latitude, longitude];

    setTimeout(() => {
        $("#map_id").empty();
        $("#var_map").html(`<div id="map_id" style="height:400px"></div>`);
    }, 300);
    setTimeout(() => {
        map = window.L.map('map_id').setView(curLocation, 16);
        const tiles = window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        const marker = window.L.marker(curLocation).addTo(map);
        // .bindPopup('<b>Hello world!</b><br />I am a popup.').openPopup();
        map.panTo(new window.L.LatLng(latitude, longitude));
    }, 1000);
}

function get_current_time(frm, fieldname, btnname){
	frm.call('get_current_time').then(r => {
        frm.set_value(fieldname, r.message);
        hide_field(frm, btnname)
    });
}

function hide_field(frm, fieldname){
	frm.set_df_property(fieldname, 'hidden', 1)
}

function show_field(frm, fieldname){
	frm.set_df_property(fieldname, 'hidden', 0)
}
