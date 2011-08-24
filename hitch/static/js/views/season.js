require(['jquery', 'hitch'], function($, hitch) {
    $(function() {
        modal = new hitch.modal({modal: $('#test-modal')});
        $('#create-team').click(function(event) {
            modal.show();
        });
    });
});