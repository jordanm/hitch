require(['jquery', 'hitch'], function($, hitch) {
    $(function() {
        hitch.install_modal_loader('#create-season-action', {
            source: {url: '/a/modify-season'},
            onshow: function(modal) {
                new hitch.form(modal.find('form'), {redirect_on_success: true});
            }
        });
    });
});