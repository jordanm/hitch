


/*
define(['jquery', 'jquery.tools', 'core'], function($, _, core) {
    var form = function(params) {
        var self = this;
        $.extend(self, params);
        self.button = params.submit_button || self.form.find('button');
        self.errors = [];
        self.marks = {};
        self.messages = [];
        self.tooltip_params = params.tooltip_params || {};
        self.tooltip = null;
        self.form.find('input:text,input:password,textarea').bind('blur', function(event) {
            var element = $(event.target);
            if(element && element.length) {
                self.revalidate(element);
            }
        });
        self.form.find('select').bind('change', function(event) {
            var element = $(event.target);
            if(element && element.length) {
                self.revalidate(element);
            }
        });
        self.form.submit(function(event) {
            return self.submit();
        });
    };
    $.extend(form.prototype, {
            
    });
    return form;
});*/


define(['jquery', 'jquery.tools', 'core'], function($, _, core) {
    var field = function(form, element, params) {
        var self = this;
        
    };


    var form = function(params) {
        var self = this;
        $.extend(self, {
            errors: [],
            form: null,
            messages: [],
            onerror: null,
            onsuccess: null,
            tooltip: null,
        });
        $.extend(self, params);
        if(typeof self.form == 'string') {
            self.form = $(self.form);
        }
        self.method = self.method || self.form.attr('method') || 'POST';
        self.url = self.url || self.form.attr('action');
        self.form.submit(function(event) {
            return self.submit();
        });
        self.form.data('form', self);
    };
    $.extend(form.prototype, {
        focus: function(element) {
            element.focus();
            if(element.is('input[type=text],input[type=password],textarea')) {
                element.select();
            }
        },
        serialize: function() {
            var data = this.form.serializeArray();
            $.each(data, function(key, value) {
                if(typeof(value) == 'number' && isNaN(value)) {
                    data[key] = '';
                }
            });
            return data;
        },
        submit: function(event) {
            var self = this;
            if(self.validate()) {
                var data = self.serialize();
                if(self.data) {
                    $.extend(data, self.data);
                }
                $.ajax({
                    cache: false,
                    data: $.param(data, true),
                    dataType: 'json',
                    type: self.method,
                    url: self.url,
                    success: function(response) {
                        if(response.messages) {
                        
                        }
                        if(response.error) {
                            if(response.field_errors) {
                            
                            }
                            if(response.form_errors) {
                            
                            }
                            self.onerror(self, response.error);
                        } else {
                            self.onsuccess(self, response);
                        }
                    },
                    error: function() {
                    }
                });
            }
            if(event) {
                event.preventDefault();
            }
            return false;        
        },
        validate: function() {
            return true;
        }
    });
    core.form = form;
});