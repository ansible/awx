/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



/**********************************************************************
 *  config.js
 *
 *  Gobal configuration variables for controlling application behavior.
 *
 *  Do NOT change this file, unless the changes should be included in
 *  production builds. For development, copy this file to local_config.js,
 *  and make changes.  git will ignore local_config.js
 *
 */

/*jshint unused:false */

(function() {

    //$.fn.modal.Constructor.DEFAULTS.backdrop = 'static';

    return {
        // custom_logo: true // load /var/lib/awx/public/static/assets/custom_console_logo.png as the login modal header.  if false, will load the standard tower console logo
        // custom_login_info: "example notice" // have a notice displayed in the login modal for users.  note that, as a security measure, custom html is not supported and will be escaped.
        tooltip_delay: { show: 500, hide: 100 }, // Default number of milliseconds to delay displaying/hiding tooltips

        debug_mode: true, // Enable console logging messages

        password_length: 8, // Minimum user password length.  Set to 0 to not set a limit
        password_hasLowercase: true, // require a lowercase letter in the password
        password_hasUppercase: false, // require an uppercase letter in the password
        password_hasNumber: true, // require a number in the password
        password_hasSymbol: false, // require one of these symbols to be
        // in the password: -!$%^&*()_+|~=`{}[]:";'<>?,./

        variable_edit_modes: { // Options we pass to ControlMirror for editing YAML/JSON variables
            yaml: {
                mode: "text/x-yaml",
                matchBrackets: true,
                autoCloseBrackets: true,
                styleActiveLine: true,
                lineNumbers: true,
                gutters: ["CodeMirror-lint-markers"],
                lint: true
            },
            json: {
                mode: "application/json",
                styleActiveLine: true,
                matchBrackets: true,
                autoCloseBrackets: true,
                lineNumbers: true,
                gutters: ["CodeMirror-lint-markers"],
                lint: true
            }
        },

        websocket_port: 8080

    };
})();
