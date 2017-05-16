/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import controller from './host-groups-associate.controller';

/* jshint unused: vars */
export default ['templateUrl', 'Wait', '$compile', '$state',
    function(templateUrl, Wait, $compile, $state) {
        return {
            restrict: 'E',
            transclude: true,
            scope: false,
            controller: controller,
            templateUrl: templateUrl('inventories/host-groups/host-groups-associate/host-groups-associate'),
            link: function(scope, element, attrs, controller, transcludefn) {

                $("body").addClass("is-modalOpen");

                //$("body").append(element);

                Wait('start');

                scope.$broadcast("linkLists");

                setTimeout(function() {
                    $('#host-groups-associate-modal').modal("show");
                }, 200);

                $('.modal[aria-hidden=false]').each(function () {
                    if ($(this).attr('id') !== 'host-groups-associate-modal') {
                        $(this).modal('hide');
                    }
                });

                scope.closeModal = function() {
                    $("body").removeClass("is-modalOpen");
                    $('#host-groups-associate-modal').on('hidden.bs.modal',
                        function () {
                            $('.AddUsers').remove();
                        });
                    $('#host-groups-associate-modal').modal('hide');

                    $state.go('^', null, {reload: true});
                };

                scope.compileList = function(html) {
                    $('#host-groups-associate-list').append($compile(html)(scope));
                };

                Wait('stop');

                window.scrollTo(0,0);
            }
        };
    }
];
