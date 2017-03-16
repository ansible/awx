/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
import addUsers from './addUsers.controller';
export default
    ['Wait', 'templateUrl', '$compile', function(Wait, templateUrl, $compile) {
            return {
                restrict: 'E',
                scope: {
                    addUsersType: '@'
                },
                controller: addUsers,
                templateUrl: templateUrl('organizations/linkout/addUsers/addUsers'),
                link: function(scope, element, attrs, ctrl) {

                    $("body").addClass("is-modalOpen");

                    $("body").append(element);

                    Wait('start');

                    scope.$broadcast("linkLists");

                    setTimeout(function() {
                        $('#add-users-modal').modal("show");
                    }, 200);

                    $('.modal[aria-hidden=false]').each(function () {
                        if ($(this).attr('id') !== 'add-users-modal') {
                            $(this).modal('hide');
                        }
                    });

                    scope.closeModal = function() {
                        $("body").removeClass("is-modalOpen");
                        $('#add-users-modal').on('hidden.bs.modal',
                            function () {
                                $('.AddUsers').remove();
                            });
                        $('#add-users-modal').modal('hide');
                    };

                    scope.$on('closeUsersModal', function() {
                        scope.closeModal();
                    });

                    scope.compileList = function(html) {
                        $('#add-users-list').append($compile(html)(scope));
                    };

                    Wait('stop');

                    window.scrollTo(0,0);
                }
            };
        }
    ];
