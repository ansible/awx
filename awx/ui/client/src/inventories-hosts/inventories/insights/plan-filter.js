/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default function(){
     return function(plan) {
         if(plan === null || plan === undefined){
             return "PLAN: Not Available <a href='https://cloud.redhat.com/insights/remediations/' target='_blank'>CREATE A NEW PLAN IN INSIGHTS</a>";
         } else {
             let name = (plan.name === null) ? "Unnamed Plan" : plan.name;
             return `<a href="https://cloud.redhat.com/insights/remediations/${plan.id}" target="_blank">${name} (${plan.id})</a>`;
         }
     };
 }
