var latitude = '';
var longitude = '';
var map;

frappe.ui.form.on("Attendance Request", {
    onload: function (frm) {        
        // frm.trigger('triggerOpenStreetMap');
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
                    status: 'Active',
                },
            };
        });
        frm.set_query("travel_request", function () {
            return {
                filters: [
                    ["employee", "=", frm.doc.employee],
                    ["docstatus", "!=", 2]
                ]
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

        clearFieldsOnLoad(frm); // Mubashir Bashir 13-03-2025
    },

    refresh: function(frm) {
        frm.trigger("show_attendance_warnings");
        frm.trigger("triggerOpenStreetMap");
        triggerCheckInOutBtn(frm);

        if (frm.is_new()) {
			frm.set_value('custom_state_data', null);
		}

        frm.trigger("showWorkFlowState"); // Mubashir Bashir 11-03-2025
        
    },
    // Start, Mubashir Bashir, 11-02-2025
	showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
			
			const desiredOrder = [
				"Applied",
				"Recommended By Line Manager",
				"Rejected By Line Manager",
				"Recommended By Head Of Department",
				"Rejected By Head Of Department",
				"Recommended by Chief Executive Officer",
				"Rejected by Chief Executive Officer",
				"Approved",
				"Rejected By Secretary General"
			];

			const orderedStates = desiredOrder
				.filter(state => stateObj.hasOwnProperty(state)) 
				.map(state => ({ key: state, ...stateObj[state] })); 
			

			let rows = ``;
			let idx = 1
			for (const data of orderedStates) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");

				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.employee_name}</td>
					<td scope="row">${data.current_state}</td>
					<td class="">${dt}</td>
					<td class="">${data.next_state}</td>
					
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Employee Name</th>
					<th class="text-left" scope="col">Current State</th>
					<th class="text-left" scope="col">DateTime</th>
					<th scope="col">Next State(Employee Name, Role)</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('custom_state_html', 'options', _html_)
		}
	},
	// Start, Mubashir Bashir, 11-03-2025
	/*showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
			
			const desiredOrder = [
				"Applied",
				"Recommended By Line Manager",
				"Rejected by the Line Manager",
				"Recommended By Head Of Department",
				"Rejected By Head Of Department",
				"Approved",
				"Rejected by Chief Executive Officer"
			];

			const orderedStates = desiredOrder
				.filter(state => stateObj.hasOwnProperty(state)) 
				.map(state => ({ key: state, ...stateObj[state] })); 
			
			let rows = ``;
			let idx = 1
			for (const data of orderedStates) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");

				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.current_user}</td>
					<td class="">${data.next_state}</td>
					<td class="">${dt}</td>
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Current State (User)</th>
					<th class="text-left" scope="col">Next State (User)</th>
					<th scope="col">DateTime</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('custom_state_html', 'options', _html_)
		}
	},*/
	// End, Mubashir Bashir, 11-03-2025

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
        get_check_in_out_miss_time(frm); // Mubashir 17-June-2025
    },

    employee: function (frm) {        
        if (frm.doc.employee) {
            // frm.trigger("set_leave_approver"); This is commentd by Mubashir due to approver set from workflow in attendance_request_utils
            frm.trigger("check_shift_assignment"); // Mubashir Bashir 12-11-2024
        }
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
    reason: function(frm){
        frm.set_value('from_time', null);
        frm.set_value('to_time', null);
        frm.set_value('travel_request', null);
        show_field(frm, 'mark_check_in');
        hide_field(frm, 'mark_check_out');
        get_check_in_out_miss_time(frm); // Mubashir 17-June-2025        
    },
    mark_check_in: function(frm){
        hide_field(frm, 'mark_check_in');
        show_field(frm, 'mark_check_out');
        setTimeout(() => {
            get_current_time(frm, 'from_time', 'mark_check_in');
        }, 20);
	},
	mark_check_out: function(frm) {
        const [hours, minutes, seconds] = frm.doc.from_time.split(':').map(Number);
        const formTime = new Date();
        formTime.setHours(hours, minutes, seconds || 0, 0);
        const now = new Date();
        const diffInMs = now - formTime;
        const diffInMinutes = diffInMs / (1000 * 60);
        
        if (diffInMinutes > 1) {
            hide_field(frm, 'mark_check_out');
            show_field(frm, 'to_time');
            setTimeout(() => {
                get_current_time(frm, 'to_time', 'mark_check_out');
            }, 20);
        } else {
            frappe.msgprint(__('Time interval is too short!'));
        }
    },


    before_save: function(frm) {
        if (frm.doc.reason && frm.doc.reason !== "Check In/Out Miss") {
            if (!frm.doc.from_time) {
                frappe.throw(__("Please mark check in using the 'Mark Check In' button"));
                return false;
            }
        }
    },

    before_submit: function(frm) {
        if (frm.doc.reason && frm.doc.reason !== "Check In/Out Miss") {
            if (!frm.doc.check_out) {
                frappe.throw(__("Please mark check out using the 'Mark Check Out' button"));
                return false;
            }
        }
    },
});


function CallOpenStreetMap() {
    
    if (cur_frm.doc.latitude == undefined || cur_frm.doc.longitude == undefined) {
        navigator.permissions.query({ name: 'geolocation' }).then((result) => {
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
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log(position)
                cur_frm.set_value("latitude", position.coords.latitude);
                cur_frm.set_value("longitude", position.coords.longitude);
            },
            (error) => {
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



function triggerCheckInOutBtn(frm){
    if(!frm.doc.__islocal){
        if(frm.doc.from_time!=undefined){
            hide_field(frm, 'mark_check_in');
            show_field(frm, 'mark_check_out');
            // show_field(frm, 'to_time');
        }
        if(frm.doc.to_time!=undefined && frm.doc.check_out){
            hide_field(frm, 'mark_check_out');
        }
    }else{
        if(frm.doc.from_time!=undefined){
            hide_field(frm, 'mark_check_in');
        }
        if(frm.doc.to_time!=undefined){
            hide_field(frm, 'mark_check_out');
        }
    }
    if (frm.doc.reason && frm.doc.reason !== "Check In/Out Miss") {
        if (frm.doc.check_out) {
            show_field(frm, 'to_time');
        }
        else {
            hide_field(frm, 'to_time');
        }
    }
}
function get_current_time(frm, fieldname, btnname){    
    frm.call('get_current_time').then(r => {
        frm.set_value(fieldname, r.message);
        if (btnname === 'mark_check_out') {
            frm.doc.check_out = true;
            frm.save();
        }
    });
}

function hide_field(frm, fieldname){
	frm.set_df_property(fieldname, 'hidden', 1)
}

function show_field(frm, fieldname){
	frm.set_df_property(fieldname, 'hidden', 0)
}

// Mubashir Bashir 13-03-2025 Start
function clearFieldsOnLoad(frm) {
    if (frm.is_new()) {
        frm.set_value('custom_next_workflow_state', '');
        frm.set_value('custom_workflow_indication', '');
        frm.set_value('custom_state_data', '');
        frm.set_value('custom_state_html', '');
        if (frm.doc.employee) {
            // frm.trigger("set_leave_approver"); This is commentd by Mubashir due to approver set from workflow in attendance_request_utils
            frm.trigger("check_shift_assignment");
        }
    }
}
// Mubashir Bashir 13-03-2025 End

// start: Mubashir Bashir, 12-11-2024
function get_check_in_out_miss_time(frm) {
    if (frm.doc.reason != 'Check In/Out Miss') return
    if (frm.doc.employee && frm.doc.from_date) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Attendance",
                fields: ["in_time", "out_time", "custom_in_times", "custom_out_times"],
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
                    
                    // Only set from_time if it hasn't been set by the button
                    if (attendance.custom_in_times && !frm.doc.from_time) {
                        // const inTime = attendance.in_time.substring(11, 19);                    
                        const inTime = attendance.custom_in_times;
                        frm.set_value("from_time", inTime);
                    }
                    
                    // Only set to_time if it hasn't been set by the button
                    if (attendance.custom_out_times && !frm.doc.to_time) {
                        // const outTime = attendance.out_time.substring(11, 19);                        
                        const outTime = attendance.custom_out_times
                        frm.set_value("to_time", outTime);
                    }
                } else {
                    console.log("No attendance record found for the selected date.");
                }
            }
        });
    }
}
// end: Mubashir Bashir, 12-11-2024