require(['jquery', 'hitch'], function($, hitch) {
    $(function() {
        hitch.install_modal_loader('#create-season-action', {
            source: {url: '/a/modify-season'},
            title: 'Create a new season',
            onshow: function(event, modal) {
                hitch.form(modal.modal.find('form'), {redirect_on_success: true});
            }
        });
    });
});