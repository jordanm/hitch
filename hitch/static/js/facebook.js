define(['jquery', 'core'], function($, core) {
    var facebook = function(params) {
        var self = this;
        self.authenticating = false;
        self.callback = null;
        self.redirect = null;
        self.requested_properties = [];
        $.extend(self, params);
        FB.init({
            appId: self.apikey,
            cookie: true,
            status: true,
            xfbml: true
        });
        FB.Event.subscribe('auth.sessionChange', function(response) {
            self.handle_session(response);
        });    
    };
    $.extend(facebook.prototype, {
        check: function(success, failure) {
            FB.getLoginStatus(function(response) {
                if(response.session) {
                    success();
                } else {
                    failure();
                }
            });
        },
        handle_session: function(response) {
            var self = this, session = response.session;
            if(session && !self.authenticated && !self.authenticating) {
                self.authenticating = true;
                $.ajax({
                    cache: false,
                    context: self,
                    dataType: 'json',
                    type: 'POST',
                    url: self.login_url,
                    success: self.query_permissions,
                    error: self.failed
                });
            }
        },
        login: function(next) {
            var self = this;
            if(next) {
                self.redirect = next;
            }
            FB.getLoginStatus(function(response) {
                if(!response.session && !self.authenticated) {
                    FB.login(function(response) {
                        self.handle_session(response);
                    });
                } else {
                    self.handle_session(response);
                }
            });
        },
        publish: function(params) {
            var actions = params.actions || [];
            FB.ui({
                attachment: params.attachment,
                method: 'stream.publish',
                message: params.message || '',
                user_message_prompt: params.prompt || 'Publish!'
            });
        },
        redirect_user: function() {
            if(this.callback) {
                this.callback();
            } else if(this.redirect) {
                window.location = this.redirect;
            } else {
                window.location = window.location;
            }
        }
    });
    core.facebook = facebook;
});