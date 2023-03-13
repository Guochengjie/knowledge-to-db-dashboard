var $table = $('#table')
var $remove = $('#remove')
var selections = []
var prev_selections = []

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

function detailFormatter(index, row) {
    var html = []
    //$.each(row, function (key, value) {
    //  html.push('<div class="text-wrap"><b>' + key + ':</b> ' + value + '</div>')
    //})
    html.push('<div class="text-wrap"><b>Unique Attributes: </b> ' + row.attribute.join(', ') + '</div>')
    return html.join('')
}

function operateFormatter(value, row, index) {
    var url = '/task/tables/' + $table.attr("data-table-type") + '/' + $table.attr("data-table-uuid") + '/edit/' + row.category + '/' + row.table
    if (row.table.endsWith("_info")) {
        return [
            '<a class="list" href="' + url + '" title="Check Attributes">',
            '<i class="fa fa-th-list"></i>',
            '</a>  '
        ].join('')
    }
    return [
        '<a class="edit" href="javascript:void(0)" title="Edit Table Name">',
        '<i class="fa fa-edit"></i>',
        '</a>  ',
        '<a class="list" href="' + url + '" title="Check Attributes">',
        '<i class="fa fa-th-list"></i>',
        '</a>  '
    ].join('')
}

window.operateEvents = {
    'click .edit': function (e, value, row, index) {
        var changeTableNameModal = new bootstrap.Modal(document.getElementById('modalChangeName'), {});
        $("#category").val(row.category);
        $("#tableOld").val(row.table);
        $("#tableNew").val(row.table);
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
                valign: 'middle'
            }, {
                title: 'Cetegory',
                field: 'category',
                align: 'center',
                valign: 'middle',
                sortable: true,
            }, {
                field: 'table',
                title: 'Table Name',
                sortable: true,
                align: 'center'
            }, {
                field: 'number_attribute',
                title: 'Total Attributes',
                sortable: true,
                align: 'center',
            }, {
                field: 'operate',
                title: 'Item Operate',
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
            prev_selections = selections
            // save your data, here just save the current page
            selections = getIdSelections()

            // check if the last checked one is info table
            // if so, select all relevant tables
            var new_checked = selections.filter(function (v) {
                return prev_selections.indexOf(v) == -1
            })
            if (new_checked.length == 1) {
                var last_id = new_checked[0]
                var data = $table.bootstrapTable('getData');
                if (data[last_id].table.endsWith("_info")) {
                    alert('Delete ' + data[last_id].table + ' will delete all entities under the same category, and relations which include the category cannot be activated.');
                    $table.bootstrapTable('checkBy', {field: 'category', values: [data[last_id].category]});
                }
            }

        })

    $remove.click(function () {
        var ids = getIdSelections();

        var delete_table = [];

        var data = $table.bootstrapTable('getData');
        $("#deleteConfirmation").empty();
        for (var i = 0; i < ids.length; i++) {
            $("#deleteConfirmation").append("<div class=\"badge bg-info text-wrap m-1\">" + data[ids[i]].category + "/" + data[ids[i]].table + "</div>")
        }
        var deleteConfirmModal = new bootstrap.Modal(document.getElementById('modalDeleteConfirmation'), {});
        $("#modalDeleteConfirmation").attr('data-delete-list', ids)
        deleteConfirmModal.show();
    })
}

$(function () {
    initTable()
})

$("#modalChangeNameSubmit").click(function () {
    var p = $.post("/api/task/tables/" + $table.attr("data-table-type") + "/" + $table.attr("data-table-uuid") + "/rename",
        {
            "category": $("#category").val(),
            "old_name": $("#tableOld").val(),
            "new_name": $("#tableNew").val()
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

    $.post("/api/task/tables/" + $table.attr("data-table-type") + "/" + $table.attr("data-table-uuid") + "/prune", "ids=" + ids)
        .fail(function () {
            alert("Error occur when pruning tables");
        })
        .done(function () {
            $remove.prop('disabled', true)
            $table.bootstrapTable('refresh')
            $("#modalDeleteConfirmation").modal('hide');
        })
})