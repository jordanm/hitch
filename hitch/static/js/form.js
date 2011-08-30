define(['jquery', 'jquery.tools', 'core'], function($, _, core) {
    var _field_implementations = {
        'input[type=text]': {
            _resize_on_modals: true
        },
        'select': {
            _validation_event: 'change'
        },
        'textarea': {
        },
        'input': {
            _resize_on_modals: true
        }
    };
    core.field = function(form, element, params) {
        var self = this;
        $.extend(self, {
            element: element,
            form: form,
            name: element.attr('name'),
            required: false,
            selector: null,
            _resize_on_modals: false,
            _validation_event: 'blur'
        });
        $.extend(self, params);
        $.each(_field_implementations, function(selector, implementation) {
            if(element.is(selector)) {
                self.selector = selector;
                $.extend(self, implementation);
                return false;
            }
        });
        self.element.bind(self._validation_event, function(event) {
            self.validate();
        });
        self.layout();
        self.element.data('field', self);
    };
    $.extend(core.field.prototype, {
        layout: function() {
            var self = this;
            if(self._resize_on_modals && self.element.is('.modal ' + self.selector)) {
                var width = self.element.parents('.field').width() - self.element.position().left + 2;
                self.element.width(width);
            }
        },
        validate: function() {
            console.debug('validating ' + this.name);
        }
    });
    core.form = function(form, params) {
        var self = this;
        if(typeof form == 'string') {
            form = $(form);
        }
        if(form.data('form')) {
            return form.data('form');
        }
        $.extend(self, {
            errors: [],
            fields: {},
            form: form,
            messages: [],
            onerror: null,
            onsuccess: null,
            redirect_on_success: null
        });
        $.extend(self, params);
        self.method = self.method || form.attr('method') || 'POST';
        self.url = self.url || form.attr('action');
        form.find('input[name],select[name],textarea[name]').not('[type=hidden]').each(function(index) {
            var field = new core.field(self, $(this));
            self.fields[field.name] = field;
        });
        form.bind('submit', function(event) {
            return self.submit();
        });
        form.data('form', self);
    };
    $.extend(core.form.prototype, {
        serialize: function() {
            var data = this.form.serializeArray();
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
                        if(self.redirect_on_success) {
                            var url = response.url || self.redirect_on_success;
                            if(typeof url == 'string') {
                                window.location = url;
                            }                        
                        }
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
});