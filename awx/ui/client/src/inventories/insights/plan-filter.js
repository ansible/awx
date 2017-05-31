/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default function(){
     return function(plan) {
         if(plan === null || plan === undefined){
             return "PLAN: Not Available <a href='https://access.redhat.com/insights/info/' target='_blank'>CREATE A NEW PLAN IN INSIGHTS</a>";
         } else {
             let name = (plan.maintenance_plan.name === null) ? "Unnamed Plan" : plan.maintenance_plan.name;
             return `<a href="https://access.redhat.com/insights/planner/${plan.maintenance_plan.maintenance_id}" target="_blank">${name} (${plan.maintenance_plan.maintenance_id})</a>`;
         }
     };
 }
