define(['jquery', 'jquery.tools', 'core'], function($, _, core) {
    var _validate_text = function() {
        var self = this, value = this.element.val();
        if(typeof self.min_length == 'number') {
            if(value.length < self.min_length) {
                self.mark_invalid([self.label + ' must be at least ' + self.min_length + ' characters long.']);
                return false;
            }
        }
        if(typeof self.max_length == 'number') {
            if(value.length > self.max_length) {
                self.mark_invalid([self.label + ' must be at most ' + self.max_length + ' characters long.']);
                return false;
            }
        }
        if(typeof self.pattern == 'string') {
            var re = new RegExp(self.pattern);
            if(!re.test(value)) {
                self.mark_invalid([self.label + ' contains invalid characters.']);
                return false;
            }
        }
        return true;
    };
    var _field_implementations = [
        ['input[type=text],input[type=password]', {
            _resize_on_modals: true,
            _validator: _validate_text
        }],
        ['textarea', {
            _resize_on_modals: true,
            _validator: _validate_text
        }],
        ['select', {
            _validation_event: 'change'
        }],
        ['input', {
            _resize_on_modals: true
        }]
    ];
    core.field = function(form, element, params) {
        var self = this;
        $.extend(self, {
            element: element,
            errors: [],
            form: form,
            label: element.parents('.field').find('label').text().replace(':', ''),
            name: element.attr('name'),
            selector: null,
            status: 'empty',
            _resize_on_modals: false,
            _validation_event: 'blur'
        });
        $.extend(self, element.data('metadata'));
        $.extend(self, params);
        $.each(_field_implementations, function(i, candidate) {
            if(element.is(candidate[0])) {
                self.selector = candidate[0];
                $.extend(self, candidate[1]);
                return false;
            }
        });
        element.bind(self._validation_event, function(event) {
            self.validate();
        });
        self._field_container = element.parents('.field');
        self._errors_container = self._field_container.find('.field-errors'); 
        self.layout();
        element.data('field', self);
    };
    $.extend(core.field.prototype, {
        layout: function() {
            if(this._resize_on_modals && this.element.parents('.modal').length > 0) {
                this.element.width(this._field_container.width() - this.element.position().left + 2);
            }
        },
        mark_invalid: function(errors) {
            var self = this;
            self.status = 'invalid';
            self._field_container.addClass('invalid');
            self._errors_container.empty();
            $.each(errors, function(i, error) {
                self._errors_container.append($('<div class="field-error">' + error + '</div>'));
            });
        },
        mark_valid: function() {
            var self = this;
            self.status = 'valid';
            self._field_container.removeClass('invalid');
            self._errors_container.empty();        
        },
        validate: function() {
            var self = this, value = this.element.val();
            if(self.required && !value) {
                self.mark_invalid(['This field is required.']);
                return false;
            }
            if(self._validator && !self._validator()) {
                return false;
            }
            self.mark_valid();
            return true;
        }
    });
    core.button = function(form, element, params) {
        var self = this;
        $.extend(self, {
            action: element.data('action') || 'submit',
            element: element,
            form: form,
            span: element.find('span')
        });
        $.extend(self, params);
        element.bind('click', function(event) {
            form.submittal_button = self;
        });
        element.data('button', self);
    };
    $.extend(core.button.prototype, {
        disable: function() {
            var self = this;
            self.element.attr('disabled', true);
            return self;
        },
        enable: function() {
            var self = this;
            self.element.attr('disabled', false);
            return self;
        },
        spin: function() {
            var self = this, span = this.span;
            if(span.length) {
                self.element.queue(function(next) {
                    span.prepend($('<img src="/static/img/loading.gif">'));
                    next();
                }).delay(300);
            }
            return self;
        },
        unspin: function() {
            var self = this;
            if(self.element.find('img').length) {
                self.element.queue(function(next) {
                    self.element.find('img').remove();
                    next();
                });
            }
            return self;
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
            buttons: [],
            default_button: null,
            fields: {},
            form: form,
            onerror: null,
            onpostsubmit: null,
            onpresubmit: null,
            onsuccess: null,
            redirect_on_success: null,
            submittal_button: null
        });
        $.extend(self, params);
        self.method = self.method || form.attr('method') || 'POST';
        self.url = self.url || form.attr('action');
        form.find('input[name],select[name],textarea[name]').not('[type=hidden]').each(function(index) {
            var field = new core.field(self, $(this));
            self.fields[field.name] = field;
        });
        form.find('button[type=submit]').each(function(index) {
            var button = new core.button(self, $(this));
            self.buttons.push(button);
            if(button.action == 'submit') {
                self.default_button = button;
            }
        });
        form.bind('submit', function(event) {
            return self.submit();
        });
        form.data('form', self);
    };
    $.extend(core.form.prototype, {
        postsubmit: function() {
            var self = this;
            $.each(self.buttons, function(i, button) {
                button.unspin().enable();
            });
            self.submittal_button = null;
            if(self.onpostsubmit) {
                self.onpostsubmit();
            }
        },
        presubmit: function() {
            var self = this;
            if(!self.submittal_button) {
                self.submittal_button = self.default_button;
            }
            $.each(self.buttons, function(i, button) {
                button.disable();
            });
            self.submittal_button.spin();
            if(self.onpresubmit) {
                self.onpresubmit();
            }            
        },
        serialize: function() {
            var data = this.form.serializeArray();
            return data;
        },
        submit: function(event) {
            var self = this, data;
            if(self.validate()) {
                self.presubmit();
                data = self.serialize();
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
                        if(response.messages && response.messages.length) {
                            core.flash(response.messages, {source: self.form});
                        }
                        if(response.error) {
                            if(response.form_errors) {
                            
                            }
                            if(response.field_errors) {
                                $.each(response.field_errors, function(name, errors) {
                                    self.fields[name].mark_invalid(errors);
                                });
                            }
                            if(self.onerror) {
                                self.onerror(self, response.error);
                            }
                        } else {
                            if(self.redirect_on_success) {
                                var url = response.url || self.redirect_on_success;
                                if(typeof url == 'string') {
                                    window.location = url;
                                }
                            }
                            if(self.onsuccess) {
                                self.onsuccess(self, response);
                            }
                        }
                        self.postsubmit();
                    },
                    error: function() {
                        self.postsubmit();
                    }
                });
            }
            if(event) {
                event.preventDefault();
            }
            return false;        
        },
        validate: function() {
            var self = this, valid = true;
            $.each(self.fields, function(name, field) {
                if(!field.validate()) {
                    valid = false;
                }
            });
            return valid;
        }
    });
});