define(['jquery', 'jquery.tools', 'core', 'facebook', 'form'], function($, _, hitch) {
    hitch.install_modal_loader('#create-account-action', {source: {url: '/account/create'}});
    hitch.install_modal_loader('#login-action', {source: {url: '/login'}});
    window.hitch = hitch;
    return hitch;
});