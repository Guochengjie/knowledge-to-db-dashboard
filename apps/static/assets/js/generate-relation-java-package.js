$(document).ready(function () {
    $('#multiple-select-optgroup-field').select2({
        theme: "bootstrap-5",
        width: $(this).data('width') ? $(this).data('width') : $(this).hasClass('w-100') ? '100%' : 'style',
        placeholder: $(this).data('placeholder'),
        closeOnSelect: false,
    });
    $('#multiple-select-optgroup-field').on('change', function () {
        var selected = $(this).val();
        var result = "";
        for (var i = 0; i < selected.length; i++) {
            result += selected[i].replace(/\./g, "/") + "|";
        }
        $('#attributes').val(result);
    });
});