var $table = $('#table')
var $remove = $('#remove')
var selections = []

function getIdSelections() {
    return $.map($table.bootstrapTable('getSelections'), function (row) {
        return row.id;
    })
}

function responseHandler(res) {
    $.each(res.rows, function (i, row) {
        row.state = $.inArray(row.id, selections) !== -1
    })
    return res
}

function stateFormatter(value, row, index) {
    if (row.disabled === true) {
      return {
        disabled: true
      }
    }
    return value
}

function operateFormatter(value, row, index) {
  	if (row.disabled) return ""
    return [
        '<a class="edit" href="javascript:void(0)" title="Edit Table Name">',
        '<i class="fa fa-edit"></i>',
        '</a>  '
    ].join('')
}

window.operateEvents = {
    'click .edit': function (e, value, row, index) {
        var changeTableNameModal = new bootstrap.Modal(document.getElementById('modalChangeName'), {});
        $("#comment").val(row.comment);
      	$("#dataType").val(row.type);
        $("#dataTypeOld").val(row.type);
      	$("#constraints").val(row.constraint);
        $("#attrOld").val(row.attribute);
        $("#attrNew").val(row.attribute);
        $("#special-constraint").val(row.index);
        changeTableNameModal.show();
    }
}

function initTable() {
    $table.bootstrapTable('destroy').bootstrapTable({
        locale: 'en-US',
        columns: [
            [{
                field: 'state',
                checkbox: true,
                align: 'center',
                valign: 'middle',
              	formatter: stateFormatter
            }, {
                title: 'Attribute',
                field: 'attribute',
                align: 'center',
                valign: 'middle',
                sortable: true,
            }, {
                title: 'Data Type',
                field: 'type',
                align: 'center',
                valign: 'middle',
                sortable: true,
            }, {
                field: 'constraint',
                title: 'Constraints',
                sortable: false,
                align: 'center',
                class: "text-wrap"
            }, {
                field: 'index',
                title: 'Special Constraint',
                sortable: true,
                align: 'center',
                class: "text-wrap"
            }, {
                field: 'comment',
                title: 'Comment',
                sortable: false,
                align: 'left',
                class: "text-wrap"
            }, {
                field: 'operate',
                title: 'Edit',
                align: 'center',
                clickToSelect: false,
                events: window.operateEvents,
                formatter: operateFormatter
            }]
        ]
    })
    $table.on('check.bs.table uncheck.bs.table ' +
        'check-all.bs.table uncheck-all.bs.table',
        function () {
            $remove.prop('disabled', !$table.bootstrapTable('getSelections').length)
        })

    $remove.click(function () {
        var ids = getIdSelections();

      	var delete_table = [];

      	var data = $table.bootstrapTable('getData');
      	$("#deleteConfirmation").empty();

      	for (var i = 0; i < ids.length; i++) {
              delete_table.push(data[ids[i]].attribute);
          $("#deleteConfirmation").append("<div class=\"badge bg-info text-wrap m-1\">"+data[ids[i]].attribute+"["+data[ids[i]].type+"]</div>")
        }
 				var deleteConfirmModal = new bootstrap.Modal(document.getElementById('modalDeleteConfirmation'), {});
      	$("#modalDeleteConfirmation").attr('data-delete-list', delete_table)
        deleteConfirmModal.show();
    })
}

$(function () {
    initTable()
})

$("#modalChangeNameSubmit").click(function () {
    var p = $.post("/api/task/attributes/" + $table.attr("data-table-type") + "/" + $table.attr("data-table-uuid") +"/" + $table.attr("data-table-category") + "/" + $table.attr("data-table-name") + "/edit",
        {
            "attr_old": $("#attrOld").val(),
            "attr_new": $("#attrNew").val(),
            "comment": $("#comment").val(),
            "data_type": $("#dataType").val(),
            "data_type_old": $("#dataTypeOld").val(),
            "constraints": $("#constraints").val(),
            "special_constraint": $("#special-constraint").val()
        })
        .done(function (data) {
            console.log("data: ", data)
            console.log("table: ", $("#tableNew").val())
            $table.bootstrapTable('refresh')
        })
        .fail(function () {
            alert("Error occur when updating table name");
        })
        .always(function () {
            $("#modalChangeName").modal('hide');
        })
});

$("#modalDeleteSubmit").click(function () {
  var ids = $("#modalDeleteConfirmation").attr("data-delete-list");

  $.post("/api/task/attributes/" + $table.attr("data-table-type") + "/" + $table.attr("data-table-uuid") +"/" + $table.attr("data-table-category") + "/" + $table.attr("data-table-name") + "/prune", "attrs="+ids)
    .fail(function () {
    	alert("Error occur when pruning tables");
  	})
    .done(function () {
        $table.bootstrapTable('refresh');
      $remove.prop('disabled', true)
    	$("#modalDeleteConfirmation").modal('hide');
    })
})

$("button.type-btn.badge.bg-info").click(function () {
    var type = $(this).attr("data-type");
    $("#dataType").val(type);
});

$("button.constraint-btn.badge.bg-info").click(function () {
    var constraint = $(this).attr("data-constraint");
    $("#constraints").val(constraint);
});