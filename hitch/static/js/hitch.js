define(['jquery', 'jquery.tools', 'core', 'facebook', 'form'], function($, _, hitch) {
    $(function() {
        hitch.install_modal_loader('#create-account-action', {
            source: {url: '/account/create'},
            onshow: function(modal) {
                hitch.form(modal.find('form'), {redirect_on_success: true});
            }
        });
        hitch.install_modal_loader('#login-action', {
            source: {data: {next: window.location.pathname}, url:'/login'},
            onshow: function(modal) {
                hitch.form(modal.find('form'), {redirect_on_success: true});
            }
        });
    });
    window.hitch = hitch;
    return hitch;
});