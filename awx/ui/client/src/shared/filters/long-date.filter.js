/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['moment', function(moment) {
     return function(input) {
        var date;
         if(input === null || input === undefined){
             return "";
         }else {
             date = moment(input);
             return date.format('l LTS');
         }
     };
 }];
