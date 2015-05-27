/**********************************************************************
 *
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
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
    // this allows you to use the custom boostrap-datepicker for
    // system tracking, without affecting the use of the datepicker() function
    // in other parts of the application.
    var datepicker = $.fn.datepicker.noConflict();
    $.fn.systemTrackingDP = datepicker;

    return {

        tooltip_delay: {show: 500, hide: 100},   // Default number of milliseconds to delay displaying/hiding tooltips

        debug_mode: false,                       // Enable console logging messages

        password_length: 8,                      // Minimum user password length.  Set to 0 to not set a limit
        password_hasLowercase: true,             // require a lowercase letter in the password
        password_hasUppercase: true,             // require an uppercase letter in the password
        password_hasNumber: true,                // require a number in the password
        password_hasSymbol: true,                // require one of these symbols to be
                                                 // in the password: -!$%^&*()_+|~=`{}[]:";'<>?,./

        session_timeout: 1800,                   // Number of seconds before an inactive session is automatically timed out and forced to log in again.
                                                 // Separate from time out value set in API.


        variable_edit_modes: {                   // Options we pass to ControlMirror for editing YAML/JSON variables
            yaml: {
                mode:"text/x-yaml",
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
