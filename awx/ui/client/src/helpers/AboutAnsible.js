/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 * @ngdoc overview
 * @name helpers
 * @description These are helpers...figure it out :)
*/
 /**
 * @ngdoc function
 * @name helpers.function:AboutAnsible
 * @description This is the code for the About Ansible modal window that pops up with cowsay giving company/tower info and copyright information.
*/


export default
    angular.module('AboutAnsibleHelpModal', ['RestServices', 'Utilities','ModalDialog'])
        .factory('AboutAnsibleHelp', ['$rootScope', '$compile', '$location' , 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', 'CreateDialog',
            function ($rootScope, $compile , $location, Rest, GetBasePath, ProcessErrors, Wait, CreateDialog) {
                return function () {

                    var scope= $rootScope.$new(),
                    url;

                    url = GetBasePath('config');
                    Rest.setUrl(url);
                    Rest.get()
                        .success(function (data){
                            scope.$emit('BuildAboutDialog', data);
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to get: ' + url + ' GET returned: ' + status });
                        });


                    if (scope.removeDialogReady) {
                        scope.removeDialogReady();
                    }
                    scope.removeDialogReady = scope.$on('DialogReady', function() {
                       // element = angular.element(document.getElementById('about-modal-dialog'));
                       // $compile(element)(scope);
                        $('#about-modal-dialog').dialog('open');
                    });

                    if (scope.removeBuildAboutDialog) {
                        scope.removeBuildAboutDialog();
                    }
                    scope.removeBuildAboutDialog = scope.$on('BuildAboutDialog', function(e, data) {
                        var spaces, i, j,
                        paddedStr  = "",
                        str = data.version,
                        subscription = data.license_info.subscription_name || "";

                        if(str.search('-')){
                            str = str.substr(0,str.search('-'));
                        }
                        spaces = Math.floor((16-str.length)/2);
                        for( i=0; i<=spaces; i++){
                            paddedStr = paddedStr +" ";
                        }
                        paddedStr = paddedStr+str;
                        for( j = paddedStr.length; j<16; j++){
                            paddedStr = paddedStr + " ";
                        }
                        $('#about-modal-version').html(paddedStr);
                        $('#about-modal-subscription').html(subscription);
                        scope.modalOK = function(){
                            $('#about-modal-dialog').dialog('close');
                        };
                        CreateDialog({
                            id: 'about-modal-dialog',
                            scope: scope,
                            // buttons: [],
                            width: 710,
                            height: 400,
                            minWidth: 300,
                            resizable: false,
                            callback: 'DialogReady',
                            onOpen: function(){
                                $('#dialog-ok-button').focus();
                                $('#about-modal-dialog').scrollTop(0);
                                $('#about-modal-dialog').css('overflow-x', 'hidden');
                                $('.ui-widget-overlay').css('width', '100%');
                            }
                        });
                    });

                };
            }
    ]);
