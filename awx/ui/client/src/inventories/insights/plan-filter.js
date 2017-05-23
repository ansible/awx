/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default function(){
     return function(input) {
         if(input === null || input === undefined || Array.isArray(input) && input.length === 0){
             return "PLAN: Not Available <a href='https://access.redhat.com/insights/info/' target='_blank'>CREATE A NEW PLAN IN INSIGHTS</a>";
         } else {
             return `<a href="https://access.redhat.com/insights/info/" target="_blank">${input[0].maintenance_plan.name} (${input[0].id})</a>`;
         }
     };
 }
