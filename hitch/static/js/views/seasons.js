require(['jquery', 'hitch'], function($, hitch) {
    $(function() {
        hitch.install_modal_loader('#create-season-action', {
            source: {url: '/a/modify-season'},
            onshow: function(modal) {
                modal.find('form').data('form').onsuccess = function(form, response) {
                    modal.hide();
                    window.location = response.url;
                };
            }
        });
    });
});