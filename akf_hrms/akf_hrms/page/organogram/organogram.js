var chart;
var main;
frappe.pages["organogram"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Organogram",
    single_column: true,
  });
  main = page.main;
  // $("#temp-container").html(`<div id="previewicon" style="text-align:center;"> <i class="fa fa-refresh fa-spin" style="font-size:24px"></i> </div>`)
  filters.init(page);
  // console.log()
  // $("#page-organogram .page-body")
  //   .addClass("container-fluid")
  //   .removeClass("container");
  // server.make_call(page);
};
filters = {
  init: function (page) {
    filters.add(page);
    filters.actions(page);
    $(frappe.render_template("organogram")).appendTo(page.main);
  },
  add: function (page) {
    let params = {};

    let company = page.add_field({
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_default("company"),
      reqd: 1,
      change: (e) => {
        if (e.target.value) {
          // fetchDashboardData(page);
        } else {
          frappe.msgprint(__("Please select a company"));
        }
      },
    });
    let branch = page.add_field({
      fieldname: "branch",
      label: __("Branch"),
      fieldtype: "Link",
      options: "Branch",
      default: "",
      reqd: 1,
      change: (e) => {
        if (e.target.value) {
          // fetchDashboardData(page);
        } else {
          frappe.msgprint(__("Please select a branch"));
        }
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
        params = {
          "company": company.get_value(),
          "branch": branch.get_value(),
        }
        if (company.get_value() != "" && branch.get_value() != "") {
          $("#page-organogram .page-body")
            .addClass("container-fluid")
            .removeClass("container");
          server.make_call(params);
        }else{
          let msg = ``;
          msg += company.get_value()=="" ? " <b>Company</b>,": "";
          msg += branch.get_value()=="" ? " <b>Branch</b>": "";
          if(msg!=""){
            frappe.msgprint(__(`Please select filter(s): ${msg}`), title="Missing Filters");
          }
        }

      },
    });
  },
  actions: function (page) {
    let exportImage = page.set_primary_action(
      "Export",
      () => export_chart(),
      "octicon octicon-plus"
    );
    let setImage = page.set_secondary_action(
      "Set Image",
      () => setImageDimension(),
      "octicon octicon-sync"
    );
  }
}

server = {
  make_call: function (params) {
    // var startTime = performance.now()
    frappe.call({
      method: "akf_hrms.akf_hrms.page.organogram.organogram.get_children",
      async: false,
      args: {
        doctype: "Employee",
        params: params,
      },
      callback: function (r) {
        let data = r.message;
        console.log(data);
        let raw = [
          { name: 'Saad Saeed', id: 'AKFP-PK-CO-00068', parentId: '', branch: 'Central Office' },
          { name: 'Sheikh Ahsan Farid', id: 'AKFP-PK-CO-00072', parentId: 'AKFP-PK-CO-00068', branch: 'Central Office' },
          { name: 'Muhammad Bilal Arshad', id: 'AKFP-PK-CO-00125', parentId: 'AKFP-PK-CO-00068', branch: 'Central Office' }
        ];
        // var endTime = performance.now()
        // console.log(`Call to getdata took ${endTime - startTime} milliseconds`)
        loadOrgChart(data);
      },
    });

  },
};

function loadOrgChart(data) {
  chart = new d3.OrgChart()
    .container(".chart-container")
    .data(data)
    .nodeHeight((d) => 95)
    .nodeWidth((d) => {
      return 260;
    })
    .childrenMargin((d) => 50)
    .compactMarginBetween((d) => 25)
    .compactMarginPair((d) => 50)
    .siblingsMargin((d) => 25)
    .buttonContent(({ node, state }) => {
      return `<div style="px;color:#716E7B;border-radius:5px;padding:4px;font-size:10px;margin:auto auto;background-color:white;border: 1px solid #E4E2E9"> <span style="font-size:9px">${node.children
        ? `<i class="fa fa-angle-up"></i>`
        : `<i class="fa fa-angle-down"></i>`
        }</span> ${node.data._directSubordinates}  </div>`;
    })
    .linkUpdate(function (d, i, arr) {
      d3.select(this)
        .attr("stroke", (d) =>
          d.data._upToTheRootHighlighted ? "#152785" : "#E4E2E9"
        )
        .attr("stroke-width", (d) =>
          d.data._upToTheRootHighlighted ? 5 : 1
        );

      if (d.data._upToTheRootHighlighted) {
        d3.select(this).raise();
      }
    })
    .nodeContent(function (d, i, arr, state) {
      const color = "#FFFFFF";
      return `
        <div style="font-family: 'Inter', sans-serif;background-color:${color}; position:absolute;margin-top:-1px; margin-left:-1px;width:${d.width}px;height:${d.height}px;border-radius:10px;border: 1px solid #E4E2E9">
         <div style="background-color:${color};position:absolute;margin-top:-25px;margin-left:${15}px;border-radius:100px;width:50px;height:50px;" ></div>
         <img src="${d.data.img
        }" style="object-fit:cover;position:absolute;margin-top:-20px;margin-left:${20}px;border-radius:100px;width:40px;height:40px;" crossorigin="anonymous" />
         
        <div style="color:#08011E;position:absolute;right:20px;top:17px;font-size:10px;">${d.data.id
        }</div>
        <div style="font-size:14px;color:#08011E;margin-left:20px;margin-top:32px"> ${d.data.name
        } </div>
        <div style="color:#716E7B;margin-left:20px;margin-top:3px;font-size:10px;font-weight:600;"> ${d.data.title
        } </div>
          <div style="color:#716E7B;margin-left:20px;font-size:10px"> ${d.data.branch
        }</div>
          <div style="color:#716E7B;margin-left:20px;font-size:10px"> ${d.data.cluster
        }</div>

       </div>
  `;
    })
    .render();
}

function setImageDimension() {
  let chart = document.querySelector(".chart").getBoundingClientRect();
  let already_width = $(".svg-chart-container").width();
  let already_height = $(".svg-chart-container").height();
  if (chart.width > already_width) {
    already_width = chart.width + 70;
  }
  if (chart.height > already_height) {
    already_height = chart.height + 100;
  }
  $(".svg-chart-container").attr("width", already_width);
  $(".svg-chart-container").attr("height", already_height);
}
async function export_chart() {
  frappe.dom.freeze(__("Exporting..."));

  $("#hierarchy-chart-wrapper").css({
    overflow: "visible",
    position: "fixed",
    left: "0",
    top: "0",
  });
  $(".svg-chart-container").addClass("exported");
  setImageDimension();
  await html2canvas(document.querySelector("#hierarchy-chart-wrapper"), {
    allowTaint: true,
    useCORS: true,
    logging: true,

    imageTimeout: 0,
    proxy: "http://172.104.34.13:6001/",
  })
    .then(function (canvas) {
      let dataURL;
      dataURL = canvas.toDataURL("image/gif");
      console.log(dataURL);
      // download the image
      let a = document.createElement("a");
      a.href = dataURL;
      a.download = "hierarchy_chart";
      a.target = "_blank";
      a.click();
    })
    .finally(() => {
      frappe.dom.unfreeze();
    });
  $("#hierarchy-chart-wrapper").css({
    overflow: "auto",
    position: "relative",
  });
  $(".svg-chart-container").removeClass("exported");
}


// $(`<script type="text/javascript" src="https://d3js.org/d3.v7.min.js"></script>`).appendTo(document.body);
// $(`<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/d3-org-chart@2"></script>`).appendTo(document.body);
// $(`<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.3.5/jspdf.min.js"></script>`).appendTo(document.body);
// $(`<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/d3-flextree@2.1.2/build/d3-flextree.js"></script>`).appendTo(document.body);
