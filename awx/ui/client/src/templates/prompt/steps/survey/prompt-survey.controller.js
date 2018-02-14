/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [ 'TemplatesStrings', function(strings) {
            const vm = this;

            vm.strings = strings;

            let scope;
            let launch;

            vm.init = (_scope_, _launch_) => {
                scope = _scope_;
                launch = _launch_;
            };

            // This function is used to hide/show the contents of a password
            // within a form
            vm.togglePassword = (id) => {
                var buttonId = id + "_show_input_button",
                inputId = id;
                if ($(inputId).attr("type") === "password") {
                    $(buttonId).html(strings.get('HIDE'));
                    $(inputId).attr("type", "text");
                } else {
                    $(buttonId).html(strings.get('SHOW'));
                    $(inputId).attr("type", "password");
                }
            };
        }
    ];
