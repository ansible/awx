/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import MultiSelectPreviewController from './multi-select-preview.controller';

 export default ['templateUrl', function(templateUrl) {
     return {
         restrict: 'E',
         replace: true,
         scope: {
             selectedRows: '=',
             availableRows: '='
         },
         controller: MultiSelectPreviewController,
         templateUrl: templateUrl('shared/multi-select-preview/multi-select-preview')
     };
 }];
