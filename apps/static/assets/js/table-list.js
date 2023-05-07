var $table = $('#table')
var $remove = $('#remove')
var $sql_button = $('.sql')
var selections = []

function getIdSelections() {
    return $.map($table.bootstrapTable('getSelections'), function (row) {
        return row.uuid;
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
    html.push('<p><b>Description:</b> ' + row.description + '</p>')
    html.push('<p><b>UUID:</b> ' + row.uuid + '</p>')

    return html.join('')
}

function operateFormatter(value, row, index) {
    return [
        '<a href="/task/tables/entity/' + row.uuid + '" >',
        '<button type="button" class="btn btn-primary d-inline-flex align-items-center"> Edit Entities <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M.99 5.24A2.25 2.25 0 013.25 3h13.5A2.25 2.25 0 0119 5.25l.01 9.5A2.25 2.25 0 0116.76 17H3.26A2.267 2.267 0 011 14.74l-.01-9.5zm8.26 9.52v-.625a.75.75 0 00-.75-.75H3.25a.75.75 0 00-.75.75v.615c0 .414.336.75.75.75h5.373a.75.75 0 00.627-.74zm1.5 0a.75.75 0 00.627.74h5.373a.75.75 0 00.75-.75v-.615a.75.75 0 00-.75-.75H11.5a.75.75 0 00-.75.75v.625zm6.75-3.63v-.625a.75.75 0 00-.75-.75H11.5a.75.75 0 00-.75.75v.625c0 .414.336.75.75.75h5.25a.75.75 0 00.75-.75zm-8.25 0v-.625a.75.75 0 00-.75-.75H3.25a.75.75 0 00-.75.75v.625c0 .414.336.75.75.75H8.5a.75.75 0 00.75-.75zM17.5 7.5v-.625a.75.75 0 00-.75-.75H11.5a.75.75 0 00-.75.75V7.5c0 .414.336.75.75.75h5.25a.75.75 0 00.75-.75zm-8.25 0v-.625a.75.75 0 00-.75-.75H3.25a.75.75 0 00-.75.75V7.5c0 .414.336.75.75.75H8.5a.75.75 0 00.75-.75z"></path></svg></button>',
        '</a>  ',
        '<a href="/task/tables/relation/' + row.uuid + '" >',
        '<button type="button" class="btn btn-primary d-inline-flex align-items-center"> Edit Relations <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M.99 5.24A2.25 2.25 0 013.25 3h13.5A2.25 2.25 0 0119 5.25l.01 9.5A2.25 2.25 0 0116.76 17H3.26A2.267 2.267 0 011 14.74l-.01-9.5zm8.26 9.52v-.625a.75.75 0 00-.75-.75H3.25a.75.75 0 00-.75.75v.615c0 .414.336.75.75.75h5.373a.75.75 0 00.627-.74zm1.5 0a.75.75 0 00.627.74h5.373a.75.75 0 00.75-.75v-.615a.75.75 0 00-.75-.75H11.5a.75.75 0 00-.75.75v.625zm6.75-3.63v-.625a.75.75 0 00-.75-.75H11.5a.75.75 0 00-.75.75v.625c0 .414.336.75.75.75h5.25a.75.75 0 00.75-.75zm-8.25 0v-.625a.75.75 0 00-.75-.75H3.25a.75.75 0 00-.75.75v.625c0 .414.336.75.75.75H8.5a.75.75 0 00.75-.75zM17.5 7.5v-.625a.75.75 0 00-.75-.75H11.5a.75.75 0 00-.75.75V7.5c0 .414.336.75.75.75h5.25a.75.75 0 00.75-.75zm-8.25 0v-.625a.75.75 0 00-.75-.75H3.25a.75.75 0 00-.75.75V7.5c0 .414.336.75.75.75H8.5a.75.75 0 00.75-.75z"></path></svg></button>',
        '</a>  ',
        '<button type="button" class="btn btn-primary d-inline-flex align-items-center sql me-1">',
        'Generate SQL <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37zM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 013 13.179z"></path></svg>',
        '</button>',
        // '<a href="/task/sqlalchemy/relation/' + row.uuid + '" >',
        // '<button type="button" class="btn btn-primary d-inline-flex align-items-center me-1">Generate SqlAlchemy Classes <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37zM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 013 13.179z"></path></svg></button>',
        // '</a>',
        // '<a href="/task/restful-server/relation/' + row.uuid + '" >',
        // '<button type="button" class="btn btn-primary d-inline-flex align-items-center me-1">Generate FastAPI RESTful Server <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37zM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 013 13.179z"></path></svg></button>',
        // '</a>',
        '<a href="/task/java/relation/' + row.uuid + '" >',
        '<button type="button" class="btn btn-primary d-inline-flex align-items-center me-1">Generate Java Relation Package <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37zM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 013 13.179z"></path></svg></button>',
        '</a>'
        // '<button type="button" class="btn btn-primary d-inline-flex align-items-center" data-task-uuid="' + row.uuid + '">',
        // 'Generate Java Package <svg class="icon icon-xxs ms-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path clip-rule="evenodd" fill-rule="evenodd" d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37zM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 013 13.179z"></path></svg>',
        // '</button>'
    ].join('')
}

window.operateEvents = {
    'click .list': function (e, value, row, index) {
        alert('You click like action, row: ' + JSON.stringify(row))
    },
    'click .remove': function (e, value, row, index) {
        $table.bootstrapTable('remove', {
            field: 'category',
            values: [row.category]
        })
    }
}

function totalTextFormatter(data) {
    return 'Total'
}

function totalNameFormatter(data) {
    return data.length
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
                title: 'Title',
                field: 'title',
                align: 'left',
                valign: 'middle',
                sortable: true,
            }, {
                field: 'operate',
                title: 'Operate',
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
            selections = getIdSelections()
            // push or splice the selections if you want to save all data selections
            console.log(selections)
        })
    $remove.click(function () {
        var ids = getIdSelections();
        $("#deleteConfirmation").empty();

        var delete_table = [];
        var data = $table.bootstrapTable('getData');
        console.log(data)

        for (var i = 0; i < data.length; i++) {
            if (ids.includes(data[i]['uuid'])) {
                delete_table.push(data[i]['uuid']);
                $("#deleteConfirmation").append("<div class=\"badge bg-info text-wrap m-1\">" + data[i].title + "<br \>&lt;" + data[i].uuid + "&gt;</div>")
            }
        }
        var deleteConfirmModal = new bootstrap.Modal(document.getElementById('modalDeleteConfirmation'), {});
        $("#modalDeleteConfirmation").attr('data-delete-list', delete_table)
        deleteConfirmModal.show();
    })
}


$("#modalDeleteSubmit").click(function () {
    var ids = $("#modalDeleteConfirmation").attr("data-delete-list");
    $.post("/api/task/delete", "uuid_list=" + ids)
        .fail(function () {
            alert("Error occur");
        })
        .done(function (data) {
            $table.bootstrapTable('refresh');
            $remove.prop('disabled', true)
            $("#modalDeleteConfirmation").modal('hide');
        })
});


window.operateEvents = {
    'click .sql': function (e, value, row, index) {
        $.get("/api/get_sql_query/" + row.uuid)
            .fail(function () {
                alert("Error occur");
            })
            .done(function (data) {
                let result = ""
                for (let i = 0; i < data['message'].length; i++) {
                    result += data['message'][i] + "\n"
                }
                // change the .sql-viewer html content to result
                $("#sql-viewer").html(result);
                try {
                    navigator.clipboard.writeText(result);
                    console.log('Content copied to clipboard');
                } catch (err) {
                    console.error('Failed to copy: ', err);
                }
                hljs.highlightAll();
                var sqlModal = new bootstrap.Modal(document.getElementById('modal-sql'), {});
                sqlModal.show();
            })
    }
}


$(function () {
    initTable()

})