define(['jquery', 'jquery.tools', 'core'], function($, _, core) {
    var _field_implementations = {
        'input[type=text]': {
        },
        'select': {
            _validation_event: 'change'
        },
        'textarea': {
        },
        'input': {
        }
    };
    core.field = function(form, element, params) {
        var self = this;
        $.extend(self, {
            element: element,
            form: form,
            name: element.attr('name'),
            required: false,
            _validation_event: 'blur'
        });
        $.extend(self, params);
        $.each(_field_implementations, function(selector, implementation) {
            if(element.is(selector)) {
                $.extend(self, implementation);
                return false;
            }
        });
        self.element.bind(self._validation_event, function(event) {
            self.validate();
        });
        self.element.data('field', self);
    };
    $.extend(core.field.prototype, {
        validate: function() {
            console.debug('validating ' + this.name);
        }
    });
    core.form = function(params) {
        var self = this;
        $.extend(self, {
            errors: [],
            fields: {},
            form: null,
            messages: [],
            onerror: null,
            onsuccess: null
        });
        $.extend(self, params);
        if(typeof self.form == 'string') {
            self.form = $(self.form);
        }
        self.method = self.method || self.form.attr('method') || 'POST';
        self.url = self.url || self.form.attr('action');
        self.form.find('input[name],select[name],textarea[name]').not('[type=hidden]').each(function(index) {
            var field = new core.field(self, $(this));
            self.fields[field.name] = field;
        });
        self.form.bind('submit', function(event) {
            return self.submit();
        });
        self.form.data('form', self);
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