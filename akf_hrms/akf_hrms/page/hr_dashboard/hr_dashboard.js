frappe.pages['hr-dashboard'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'HR Dashboard',
		single_column: true
	});
	filters.add(page);
}

filters = {
	add: function(page){
		let filters = {}
		let company = page.add_field({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_default("company"),
			reqd: 1,
			change: (e) => {
			},
		});
		let branch = page.add_field({
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			default: "",
			reqd: 0,
			change: (e) => {
			},
		});
		let from_date = page.add_field({
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			options: "",
			default: frappe.datetime.now_date(),
			reqd: 0,
			change: (e) => {
			},
		});
		let to_date = page.add_field({
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			options: "",
			default: frappe.datetime.now_date(),
			reqd: 0,
			change: (e) => {
			},
		});
		let filters_btn = page.add_field({
			fieldname: "filters_btn",
			label: __("Filters"),
			fieldtype: "Button",
			options: "",
			default: "",
			reqd: 0,
			click: (e) => {
				filters = {
					"company": company.get_value(),
					"branch": branch.get_value(),
					"from_date": from_date.get_value(),
					"to_date": to_date.get_value(),
				}
				serverCall.fetch_counts(page, filters);
			},
		});
		// serverCall.fetch_counts(page)
	}
}
serverCall = {
	fetch_counts: function(page, filters){
		frappe.call({
			method: "akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.fetch_counts",
			args: {
				filters: filters
			}, 
			callback: function(r){
				let data = r.message;
				console.log(data)
				loadDesign.template(page, data);
			}
		})
	}
}
loadDesign = {
	template: function (page, data) {
		$("#management_dashboard_id").remove();
		const content = frappe.render_template("hr_dashboard", data);
		const main = page.main;
		$(content).appendTo(main);
		charts.employee_count_by_status();
		charts.employee_count_by_department();
		charts.employee_count_by_salary_range();
	}
}

charts = {
	employee_count_by_status: function () {
		donutChart();
	},
	employee_count_by_department: function () {
		barChart();
	},
	employee_count_by_salary_range: function () {
		pieChart()
	}
}

function donutChart() {
	Highcharts.chart('employee_by_status', {
		colors: ['#01BAF2', 'rgb(75, 208, 139)', '#FAA74B', '#B37CD2'],
		chart: {
			type: 'pie',
		},
		title: {
			text: 'School Status',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',
				fontFamily: '"Inter", sans-serif'
			}
		},
		tooltip: {
			valueSuffix: '%'
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y} %'
				},
				showInLegend: true
			}
		},
		legend: {
			align: 'left',
			verticalAlign: 'bottom',
			layout: 'horizontal',
			labelFormat: '<b>{name}</b>',
			itemWidth: 150 // Adjust the width of each legend item
		},
		series: [{
			name: 'Percentage',
			colorByPoint: true,
			innerSize: '80%',
			data: [{
				name: 'Open School',
				y: 78
			},
			{
				name: 'Closed During Visit',
				y: 20.9
			},
			{
				name: 'Permanent Closed',
				y: 20.9
			},
			{
				name: 'Temporary Closed',
				y: 2.1
			}
			]
		}],
		credits: {
			enabled: false // Disable credits
		} 
	});

	
	Highcharts.chart('open_position', {
		colors: ['#01BAF2', 'rgb(75, 208, 139)', '#FAA74B', '#B37CD2'],
		chart: {
			type: 'pie',
		},
		title: {
			text: 'Open Position By Department',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',
				fontFamily: '"Inter", sans-serif'
			}
		},
		tooltip: {
			valueSuffix: '%'
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y} %'
				},
				showInLegend: true
			}
		},
		legend: {
			align: 'left',
			verticalAlign: 'bottom',
			layout: 'horizontal',
			labelFormat: '<b>{name}</b>',
			itemWidth: 150 // Adjust the width of each legend item
		},
		series: [{
			name: 'Percentage',
			colorByPoint: true,
			innerSize: '80%',
			data: [{
				name: 'Open School',
				y: 78
			},
			{
				name: 'Closed During Visit',
				y: 20.9
			},
			{
				name: 'Permanent Closed',
				y: 20.9
			},
			{
				name: 'Temporary Closed',
				y: 2.1
			}
			]
		}],
		credits: {
			enabled: false // Disable credits
		} 
	});
}
function barChart() {
	Highcharts.chart('employee_count', {
		chart: {
			type: 'column'
		}, 
		title: {
			text: 'Employee count By department',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',    
				fontFamily: '"Inter", sans-serif'
			}
		},
		subtitle: {
			align: 'left',
			text: ''
		},
		exporting: {
			enabled: false,
		},
		credits: {
			enabled: false
		},
		accessibility: {
			announceNewData: {
				enabled: true
			}
		},
		xAxis: {
			type: 'category'
		},
		yAxis: {
			title: {
				text: ''
			}

		},
		legend: {
			enabled: false
		},
		plotOptions: {
			series: {
				borderWidth: 0,
				dataLabels: {
					enabled: true,
					format: '{point.y}'
				}
			}
		},

		tooltip: {
			headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
			pointFormat: '<span style="color:{point.color}">{point.name}</span>: ' +
				'<b>{point.y}</b> of total<br/>'
		},

		series: [
			{
				name: 'Employees',
				colorByPoint: true,
				data: [
					{
						name: 'Chrome',
						y: 63.06
					},
					{
						name: 'Safari',
						y: 19.84
					},
					{
						name: 'Firefox',
						y: 4.18
					},
					{
						name: 'Edge',
						y: 4.12
					},
					{
						name: 'Opera',
						y: 2.33
					},
					{
						name: 'Internet Explorer',
						y: 0.45
					},
					{
						name: 'Other',
						y: 1.582
					}
				]
			}
		],

	});

	Highcharts.chart('application_received', {
		chart: {
			type: 'column'
		}, 
		title: {
			text: 'Application Recevied By Source',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',    
				fontFamily: '"Inter", sans-serif'
			}
		},
		subtitle: {
			align: 'left',
			text: ''
		},
		exporting: {
			enabled: false,
		},
		credits: {
			enabled: false
		},
		accessibility: {
			announceNewData: {
				enabled: true
			}
		},
		xAxis: {
			type: 'category'
		},
		yAxis: {
			title: {
				text: ''
			}

		},
		legend: {
			enabled: false
		},
		plotOptions: {
			series: {
				borderWidth: 0,
				dataLabels: {
					enabled: true,
					format: '{point.y}'
				}
			}
		},

		tooltip: {
			headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
			pointFormat: '<span style="color:{point.color}">{point.name}</span>: ' +
				'<b>{point.y}</b> of total<br/>'
		},

		series: [
			{
				name: 'Employees',
				colorByPoint: true,
				data: [
					{
						name: 'Chrome',
						y: 63.06
					},
					{
						name: 'Safari',
						y: 19.84
					},
					{
						name: 'Firefox',
						y: 4.18
					},
					{
						name: 'Edge',
						y: 4.12
					},
					{
						name: 'Opera',
						y: 2.33
					},
					{
						name: 'Internet Explorer',
						y: 0.45
					},
					{
						name: 'Other',
						y: 1.582
					}
				]
			}
		],

	});
}
function pieChart() {
	Highcharts.chart('salary_range', {
		chart: {
			type: 'pie'
		}, 
		title: {
			text: '  Employee count By salary range',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',
				fontFamily: '"Inter", sans-serif'
			}
		},
		tooltip: {
			valueSuffix: '%'
		},
		subtitle: {
			text:
				''
		},
		exporting: {
			enabled: false,
		},
		credits: {
			enabled: false
		},

		plotOptions: {
			series: {
				allowPointSelect: true,
				cursor: 'pointer',
				dataLabels: [{
					enabled: true,
					distance: 20
				}, {
					enabled: true,
					distance: -40,
					format: '{point.percentage:.1f}%',
					style: {
						fontSize: '1.2em',
						textOutline: 'none',
						opacity: 0.7
					},
					filter: {
						operator: '>',
						property: 'percentage',
						value: 10
					}
				}]
			}
		},
		series: [
			{
				name: 'Percentage',
				colorByPoint: true,
				data: [
					{
						name: 'Water',
						y: 55.02
					},
					{
						name: 'Fat',
						sliced: true,
						selected: true,
						y: 26.71
					},
					{
						name: 'Carbohydrates',
						y: 1.09
					},
					{
						name: 'Protein',
						y: 15.5
					},
					{
						name: 'Ash',
						y: 1.68
					}
				]
			}
		]
	});

}