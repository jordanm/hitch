define(['jquery', 'jquery.tools', 'core'], function($, _, core) {
    core.widget = core.declare({
        resize_on_modals: false,
        validation_events: 'blur',
        initialize: function(field) {
            var self = this;
            self.field = field;        
        },
        bind: function() {
            var self = this;
            self.field.element.bind(self.validation_events, function(event) {
                self.field.validate();
            });
        },
        construct: function() {
        },
        get_value: function() {
            return this.field.element.val();
        },
        set_value: function(value) {
            this.field.element.val(value);
        },
        validate: function(value) {
            return true;        
        }
    });
    core.widget.checkbox = core.declare(core.widget, {
        get_value: function() {
            return this.field.element.is(':checked');
        },
        set_value: function(value) {
            this.field.element.attr('checked', value);
        }
    });
    core.widget.date = core.declare(core.widget, {
        preferred_width: 190,
        construct: function() {
            return this.field.element.dateinput();        
        }
    });
    core.widget.number = core.declare(core.widget, {
        preferred_width: 80,
        validation_events: 'blur textchange',
        validation_pattern: /^-?[0-9]*(?:[.][0-9]+)?/,
        validate: function(value) {
            var self = this, field = this.field;
            var numeric_value = Number(value.replace(',', ''));
            if($.isNaN(numeric_value)) {
                field.mark_invalid([field.label + ' must numeric.']);
                return false;
            }
            if(typeof field.min_value == 'number') {
                if(value < field.min_value) {
                    field.mark_invalid([field.label + ' must be greater then or equal to ' + field.min_value + '.']);
                    return false;
                }
            }
            if(typeof field.max_value == 'number') {
                if(value > field.max_value) {
                    field.mark_invalid([field.label + ' must be less then or equal to ' + field.max_value + '.']);
                    return false;
                }
            }
            return true;
        }
    });
    core.widget.textbox = core.declare(core.widget, {
        resize_on_modals: true,
        validation_events: 'blur textchange',
        validate: function(value) {
            var self = this, field = this.field;
            if(typeof field.min_length == 'number') {
                if(value.length < field.min_length) {
                    field.mark_invalid([field.label + ' must be at least ' + field.min_length + ' characters long.']);
                    return false;
                }
            }
            if(typeof field.max_length == 'number') {
                if(value.length > field.max_length) {
                    field.mark_invalid([field.label + ' must be at most ' + field.max_length + ' characters long.']);
                    return false;
                }
            }
            if(typeof field.pattern == 'string') {
                var re = new RegExp(field.pattern);
                if(!re.test(value)) {
                    field.mark_invalid([field.label + ' contains invalid characters.']);
                    return false;
                }
            }
            return true;
        }
    });
    core.widget.slug = core.declare(core.widget.textbox, {
        slugify: function(value) {
            value = value.replace(/[^\w\s-]/g, '').replace(/[-\s]+/g, '-').replace(/^[-\s]*/, '');
            return value.replace(/[-\s]*$/, '').toLowerCase();        
        },
        construct: function() {
            var self = this;
            if(self.field.slug_source_field) {
                var source = self.field.form.fields[self.field.slug_source_field].element;
                source.bind('textchange', function() {
                    self.field.element.val(self.slugify(source.val()));
                    self.field.validate();
                });
            }
        }
    });
    core.field = core.declare({
        widgets: [
            ['input[type=checkbox]', core.widget.checkbox],
            ['input[type=date]', core.widget.date],
            ['input[type=text][data-datatype=number]', core.widget.number],
            ['input[type=text][data-datatype=slug]', core.widget.slug],
            ['input[type=text],input[type=password]', core.widget.textbox],
            ['textarea', core.widget.textarea],
            ['select', core.widget.selectbox],
            ['input', core.widget.textbox]
        ],
        initialize: function(form, element, params) {
            var self = this, reconstructed_element;
            $.extend(self, {
                element: element,
                form: form,
                initial_value: null,
                label: element.parents('.field').find('label').text().replace(':', ''),
                name: element.attr('name'),
                selector: null,
                status: 'unknown',
                widget: null
            });
            $.extend(self, element.data('metadata'));
            $.extend(self, params);
            $.each(self.widgets, function(i, candidate) {
                if(element.is(candidate[0])) {
                    self.selector = candidate[0];
                    self.widget = candidate[1](self);
                    return false;
                }
            });
            self.initial_value = self.get_value();
            reconstructed_element = self.widget.construct();
            if(reconstructed_element) {
                self.element = reconstructed_element;
            }
            self.widget.bind();
            self.field_container = self.element.parents('.field');
            self.errors_container = self.field_container.find('.field-errors');
            self.layout();
            self.element.data('field', self);
        },
        get_value: function() {
            return this.widget.get_value();
        },
        layout: function() {
            var self = this;
            if(self.preferred_width) {
                self.element.width(self.preferred_width);
            } else if(self.widget.preferred_width) {
                self.element.width(self.widget.preferred_width);
            } else if(self.widget.resize_on_modals && self.form.modal) {
                self.element.width(self.field_container.width() - self.element.position().left + 2);
            }
        },
        mark_invalid: function(errors) {
            var self = this;
            self.status = 'invalid';
            self.field_container.addClass('invalid');
            self.errors_container.empty();
            $.each(errors, function(i, error) {
                self.errors_container.append($('<div class="field-error">' + error + '</div>'));
            });
        },
        mark_valid: function() {
            var self = this;
            self.status = 'valid';
            self.field_container.removeClass('invalid');
            self.errors_container.empty();        
        },
        mark_unknown: function() {
            var self = this;
            self.status = 'unknown';
            self.field_container.removeClass('valid invalid');
            self.errors_container.empty();
        },
        reset: function() {
            var self = this;
            self.mark_unknown();
            self.set_value(self.initial_value);
        },
        set_value: function(value) {
            this.widget.set_value(value);
        },
        validate: function() {
            var self = this, value = this.get_value();
            if(self.required && !value) {
                self.mark_invalid(['This field is required.']);
                return false;
            }
            if(!self.widget.validate(value)) {
                return false;
            }
            self.mark_valid();
            return true;
        }
    });
    core.button = core.declare({
        initialize: function(form, element, params) {
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
        },
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
    core.form = core.declare({
        initialize: function(form, params) {
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
                modal: null,
                onerror: null,
                onpostsubmit: null,
                onpresubmit: null,
                onsuccess: null,
                redirect_on_success: null,
                reset_on_modal_close: true,
                submittal_button: null
            });
            $.extend(self, params);
            self.method = self.method || form.attr('method') || 'POST';
            self.url = self.url || form.attr('action');
            if(form.parents('.modal').length) {
                self.modal = form.parents('.modal').data('modal');
                if(self.reset_on_modal_close) {
                    self.modal.bind('onclose', function() {
                        self.reset();
                    });
                }
            }
            form.find('input[name],select[name],textarea[name]').not('[type=hidden]').each(function(index) {
                var field = core.field(self, $(this));
                self.fields[field.name] = field;
            });
            form.find('button[type=submit]').each(function(index) {
                var button = core.button(self, $(this));
                self.buttons.push(button);
                if(button.action == 'submit') {
                    self.default_button = button;
                }
            });
            form.bind('submit', function(event) {
                return self.submit();
            });
            form.data('form', self);
        },
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
        reset: function() {
            var self = this;
            $.each(self.fields, function(name, field) {
                field.reset();
            });
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