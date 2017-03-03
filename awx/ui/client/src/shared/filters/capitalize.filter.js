/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default [function() {
     return function(input) {
         input = input.charAt(0).toUpperCase() + input.substr(1).toLowerCase();
         return input;
     };
 }];
