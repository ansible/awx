/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import addPermissionsController from './addPermissions.controller';

/* jshint unused: vars */
export default
    [     'templateUrl',
        'Wait',
        function(templateUrl, Wait) {
            return {
                restrict: 'E',
                scope: true,
                controller: addPermissionsController,
                templateUrl: templateUrl('access/addPermissions/addPermissions'),
                link: function(scope, element, attrs, ctrl) {
                    scope.toggleFormTabs('users');

                    $("body").append(element);

                    Wait('start');

                    scope.$broadcast("linkLists");

                    setTimeout(function() {
                        $('#add-permissions-modal').modal("show");
                    }, 200);

                    $('.modal[aria-hidden=false]').each(function () {
                        if ($(this).attr('id') !== 'add-permissions-modal') {
                            $(this).modal('hide');
                        }
                    });

                    scope.closeModal = function() {
                        $('#add-permissions-modal').on('hidden.bs.modal',
                            function () {
                                $('.AddPermissions').remove();
                            });
                        $('#add-permissions-modal').modal('hide');
                    };

                    Wait('stop');

                    window.scrollTo(0,0);
                }
            };
        }
    ];
