define(['jquery', 'jquery.tools', 'core', 'facebook', 'form'], function($, _, hitch) {
    $('#create-account-action').click(function(event) {
        var modal = $(this).data('modal');
        if(modal) {
            modal.show();
        } else {
            $(this).data('modal', new hitch.modal({
                show_immediately: true,
                source: {url: '/account/create'}
            }));
        }
    });
    $('#login-action').click(function(event) {
        var modal = $(this).data('modal');
        if(modal) {
            modal.show();
        } else {
            $(this).data('modal', new hitch.modal({
                show_immediately: true,
                source: {url: '/login'}
            }));
        }
    });
    window.hitch = hitch;
    return hitch;
});