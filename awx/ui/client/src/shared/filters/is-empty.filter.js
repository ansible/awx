/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default function() {
     return function (obj) {
         var key;
         for (key in obj) {
             if (obj.hasOwnProperty(key)) {
                 return false;
             }
         }
         return true;
     };
 }
