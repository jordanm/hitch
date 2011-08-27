require(['jquery', 'hitch'], function($, hitch) {
    $(function() {
        hitch.install_modal_loader('#create-season-action', {source: {url: '/a/modify-season'}});
    });
});