/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import authenticationController from './loginModal.controller';

/* jshint unused: vars */
export default
    [     'templateUrl',
        'Wait',
        function(templateUrl, Wait) {
            return {
                restrict: 'E',
                scope: true,
                controller: authenticationController,
                templateUrl: templateUrl('login/loginModal/loginModal'),
                link: function(scope, element, attrs) {
                    var setLoginFocus = function () {
                        // Need to clear out any open dialog windows that might be open when this modal opens.
                        $('#login-username').focus();
                    };

                    setLoginFocus();

                    // Hide any lingering modal dialogs
                    $('.modal[aria-hidden=false]').each(function () {
                        if ($(this).attr('id') !== 'login-modal') {
                            $(this).modal('hide');
                        }
                    });

                    // Just in case, make sure the wait widget is not active
                    // and scroll the window to the top
                    Wait('stop');
                    window.scrollTo(0,0);

                    // Set focus to username field
                    $('#login-modal').on('shown.bs.modal', function () {
                        setLoginFocus();
                    });

                    $('#login-password').bind('keypress', function (e) {
                        var code = (e.keyCode ? e.keyCode : e.which);
                        if (code === 13) {
                            $('#login-button').click();
                        }
                    });

                    scope.reset = function () {
                        $('#login-form input').each(function () {
                            $(this).val('');
                        });
                    };
                }
            };
        }
    ];
