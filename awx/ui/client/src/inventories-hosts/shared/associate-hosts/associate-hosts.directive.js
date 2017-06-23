/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import controller from './associate-hosts.controller';

/* jshint unused: vars */
export default ['templateUrl', 'Wait', '$compile', '$state',
    function(templateUrl, Wait, $compile, $state) {
        return {
            restrict: 'E',
            transclude: true,
            scope: {
                saveFunction: '&'
            },
            controller: controller,
            templateUrl: templateUrl('inventories-hosts/shared/associate-hosts/associate-hosts'),
            link: function(scope, element, attrs, controller, transcludefn) {

                $("body").addClass("is-modalOpen");

                //$("body").append(element);

                Wait('start');

                scope.$broadcast("linkLists");

                setTimeout(function() {
                    $('#associate-hosts-modal').modal("show");
                }, 200);

                $('.modal[aria-hidden=false]').each(function () {
                    if ($(this).attr('id') !== 'associate-hosts-modal') {
                        $(this).modal('hide');
                    }
                });

                scope.closeModal = function() {
                    $("body").removeClass("is-modalOpen");
                    $('#associate-hosts-modal').on('hidden.bs.modal',
                        function () {
                            $('.AddUsers').remove();
                        });
                    $('#associate-hosts-modal').modal('hide');

                    $state.go('^', null, {reload: true});
                };

                scope.compileList = function(html) {
                    $('#associate-hosts-list').append($compile(html)(scope));
                };

                Wait('stop');

                window.scrollTo(0,0);
            }
        };
    }
];
