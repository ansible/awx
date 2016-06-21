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
                    console.info(attrs);
                    scope.withoutTeamPermissions = attrs.withoutTeamPermissions;
                    scope.toggleFormTabs('users');

                    $("body").addClass("is-modalOpen");

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
                        $("body").removeClass("is-modalOpen");
                        $('#add-permissions-modal').on('hidden.bs.modal',
                            function () {
                                $('.AddPermissions').remove();
                            });
                        $('#add-permissions-modal').modal('hide');
                    };

                    scope.$on('closePermissionsModal', function() {
                        scope.closeModal();
                    });

                    Wait('stop');

                    window.scrollTo(0,0);
                }
            };
        }
    ];
