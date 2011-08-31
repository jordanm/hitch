define(['jquery', 'jquery.tools'], function($) {
    function declare(implementation) {
        var declaration = function(args) {
            console.debug('called');
            if(this instanceof arguments.callee) {
                console.debug('callee correct');
                if(typeof this.initialize == 'function') {
                    console.debug(args);
                    
                    this.initialize.apply(this, args.callee ? args : arguments);
                }
            } else {
                console.debug('called not correct; recalling with new');
                return new arguments.callee(arguments);
            }
        };
        if(typeof implementation != 'undefined') {
            $.extend(declaration.prototype, implementation);
        }
        return declaration;
    };
    var modal = function(params) {
        $.extend(this, {
            closeable: true,
            close_button: '.modal-close-button',
            expose: {color: '#444', loadSpeed: 200, opacity: 0.8, zIndex: 500},
            exposed: true,
            modal: null,
            onhide: null,
            onload: null,
            onshow: null,
            remove_on_close: false,
            show_immediately: false,
            top: '10%'
        });
        $.extend(this, params);
        if(this.source) {
            this.load();
        } else {
            this.construct();
        }
    };
    $.extend(modal.prototype, {
        construct: function(loading) {
            var modal = this.modal;
            if(!this.closeable) {
                modal.find(this.close_button).remove();
            }
            if(!modal.parents().length) {
                $('body').append(modal);
            }
            if(!modal.data('overlay')) {
                var options = {api: true, close: this.close_button, top: this.top};
                if(this.exposed) {
                    options.expose = this.expose;
                }
                if(!this.closeable) {
                    options.closeOnClick = options.closeOnEsc = false;
                }
                if(this.remove_on_close) {
                    options.onClose = function(event) {
                        modal.remove();
                    };
                }
                modal.overlay(options);
            }
            if(!loading && this.show_immediately) {
                this.show();
            }
        },
        hide: function(remove) {
            this.modal.overlay().close();
            if(remove) {
                this.modal.remove();
            } else if(this.onhide) {
                this.onhide(self.modal);
            }
        },
        load: function() {
            var self = this, source = this.source;
            $.ajax({
                cache: false,
                data: source.data,
                dataType: 'html',
                type: source.method || 'GET',
                url: source.url,
                success: function(response) {
                    self.modal = $(response);
                    self.construct(true);
                    if(self.onload) {
                        self.onload(self.modal);
                    }
                    if(self.show_immediately) {
                        self.show();
                    }
                }
            });                    
        },
        show: function() {
            this.modal.overlay().load();
            if(this.onshow) {
                this.onshow(this.modal);
            }
        }
    });
    return {
        cookie: function(name, value, options) {
            if(typeof value != 'undefined') {
                options = options || {};
                if(value === null) {
                    value = '';
                    options.expires = -1;
                }
                if(!options.path) {
                    options.path = '/';
                }
                var expires = '';
                if(options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
                    var date;
                    if(typeof options.expires == 'number') {
                        date = new Date();
                        date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
                    } else {
                        date = options.expires;
                    }
                    expires = '; expires=' + date.toUTCString();
                }
                var path = (options.path ? '; path=' + (options.path) : '');
                var domain = (options.domain ? '; domain=' + (options.domain) : '');
                var secure = (option.secure ? '; secure' : '');
                document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
            } else if(document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for(var i = 0; i < cookies.length; i++) {
                    var cookie = $.trim(cookies[i]);
                    if(cookie.substring(0, name.length + 1) == (name + '=')) {
                        return decodeURIComponent(cookie.substring(name.length + 1));
                    }
                }
            }
        },
        debug: function() {
            if(window.location.search.search('_jsdebug') >= 0) {
                $.each(arguments, function(i, argument) {
                    console.debug(argument);
                });
            }
        },
        declare: declare,
        flash: function(messages, params) {
            var container, permanent, receiver;
            if(!$.isArray(messages)) {
                if($.isPlainObject(messages)) {
                    messages = [messages];
                } else {
                    messages = [{text: 'An unknown error has occurred.', tag: 'error'}];
                }
            }
            if(!messages.length) {
                return;
            }
            params = params || {};
            if(params.source) {
                container = $(params.source).parents('.flash-message-container').first();
                if(container.length) {
                    receiver = container.find('.flash-message-receiver');
                }
            }
            if(!(receiver && receiver.length)) {
                receiver = $('.flash-message-receiver').first();
                if(!(receiver && receiver.length)) {
                    return;
                }
            }
            if(params.clear) {
                receiver.empty();
            }
            permanent = false;
            $.each(messages, function(i, message) {
                receiver.append($('<li class="' + message.tag + '">' + message.text + '</li>'));
                if(message.tag == 'error' || message.tag == 'warning') {
                    permanent = true;
                }
            });
            if(receiver.is('.nofading')) {
                receiver.show();
                if(!permanent) {
                    setTimeout(function() {receiver.hide().empty()}, 3000);
                }
            } else {
                receiver.fadeIn(500);
                if(!permanent) {
                    setTimeout(function() {receiver.fadeOut(500, function() {receiver.hide().empty()})}, 3000);
                }
            }
        },
        install_modal_loader: function(selector, params) {
            var self = this;
            $(selector).click(function(event) {
                var modal = $(this).data('modal');
                if(modal) {
                    modal.show();
                } else {
                    params.show_immediately = true;
                    $(this).data('modal', new self.modal(params));
                }
            });
        },
        modal: modal,
        post: function(params) {
            var data = '', self = this;
            if(params.data) {
                data = $.param(params.data);
            }
            $.ajax({
                cache: false,
                data: data,
                type: 'POST',
                url: params.url,
                success: function(response) {
                    if(response) {
                        if(response.messages) {
                            $.each(response.messages, function(i, item) {
                                self.flash(item);
                            });
                        }
                        if(response.error) {
                            if(params.onfailure) {
                                params.onfailure(response);
                            }
                        } else if(params.redirect_on_success) {
                            window.location = params.redirect_on_success;
                        } else if(params.reload_on_success) {
                            window.location = window.location;
                        } else if(params.onsuccess) {
                            params.onsuccess(response);
                        }
                    } else if(params.onerror) {
                        params.onerror();
                    }
                },
                error: function() {
                    if(params.onerror) {
                        params.onerror();
                    }
                }
            });
        },
        tooltip: function(params) {
            var tooltip = params.tooltip || $('#tooltip'), anchor = params.anchor;
            if(anchor && anchor.length) {
                tooltip.find('.tooltip-content').text(params.text);
                var api = anchor.tooltip({
                    api: true,
                    events: {input: 'nothing,nothing', widget: 'nothing,nothing'},
                    offset: params.offset || [0, 0],
                    opacity: params.opacity || 1.0,
                    position: params.position || 'top center',
                    tip: '#' + tooltip.attr('id')
                });
                if(!params.noshow) {
                    api.show();
                }
                return api;            
            }        
        }
    };    
});