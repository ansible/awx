export default function BuildDescription(BuildAnchor, $log, i18n) {
     return function (activity) {

         var pastTense = function(operation){
             return (/e$/.test(activity.operation)) ? operation + 'd ' : operation + 'ed ';
         };
         // convenience method to see if dis+association operation involves 2 groups
         // the group cases are slightly different because groups can be dis+associated into each other
         var isGroupRelationship = function(activity){
             return activity.object1 === 'group' && activity.object2 === 'group' && activity.summary_fields.group.length > 1;
         };

         // Activity stream objects will outlive the resources they reference
         // in that case, summary_fields will not be available - show generic error text instead
         try {
             activity.description = pastTense(activity.operation);
             switch(activity.object_association){
                 // explicit role dis+associations
                 case 'role':
                     // object1 field is resource targeted by the dis+association
                     // object2 field is the resource the role is inherited from
                     // summary_field.role[0] contains ref info about the role
                     switch(activity.operation){
                         // expected outcome: "disassociated <object2> role_name from <object1>"
                         case 'disassociate':
                             if (isGroupRelationship(activity)){
                                 activity.description += BuildAnchor(activity.summary_fields.group[1], activity.object2, activity) + activity.summary_fields.role[0].role_field +
                                     ' from ' + BuildAnchor(activity.summary_fields.group[0], activity.object1, activity);
                             }
                             else{
                                 activity.description += BuildAnchor(activity.summary_fields[activity.object2][0], activity.object2, activity) + activity.summary_fields.role[0].role_field +
                                 ' from ' + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity);
                             }
                             break;
                         // expected outcome: "associated <object2> role_name to <object1>"
                         case 'associate':
                             if (isGroupRelationship(activity)){
                                 activity.description += BuildAnchor(activity.summary_fields.group[1], activity.object2, activity) + activity.summary_fields.role[0].role_field +
                                     ' to ' + BuildAnchor(activity.summary_fields.group[0], activity.object1, activity);
                             }
                             else{
                                 activity.description += BuildAnchor(activity.summary_fields[activity.object2][0], activity.object2, activity) + activity.summary_fields.role[0].role_field +
                                 ' to ' + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity);
                             }
                             break;
                     }
                     break;
                 // inherited role dis+associations (logic identical to case 'role')
                 case 'parents':
                     // object1 field is resource targeted by the dis+association
                     // object2 field is the resource the role is inherited from
                     // summary_field.role[0] contains ref info about the role
                     switch(activity.operation){
                         // expected outcome: "disassociated <object2> role_name from <object1>"
                         case 'disassociate':
                             if (isGroupRelationship(activity)){
                                 activity.description += activity.object2 + BuildAnchor(activity.summary_fields.group[1], activity.object2, activity) +
                                     'from ' + activity.object1 + BuildAnchor(activity.summary_fields.group[0], activity.object1, activity);
                             }
                             else{
                                 activity.description += BuildAnchor(activity.summary_fields[activity.object2][0], activity.object2, activity) + activity.summary_fields.role[0].role_field +
                                 ' from ' + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity);
                             }
                             break;
                         // expected outcome: "associated <object2> role_name to <object1>"
                         case 'associate':
                             if (isGroupRelationship(activity)){
                                 activity.description += activity.object1 + BuildAnchor(activity.summary_fields.group[0], activity.object1, activity) +
                                     'to ' + activity.object2 + BuildAnchor(activity.summary_fields.group[1], activity.object2, activity);
                             }
                             else{
                                 activity.description += BuildAnchor(activity.summary_fields[activity.object2][0], activity.object2, activity) + activity.summary_fields.role[0].role_field +
                                 ' to ' + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity);
                             }
                             break;
                     }
                     break;
                 // CRUD operations / resource on resource dis+associations
                 default:
                     switch(activity.operation){
                         // expected outcome: "disassociated <object2> from <object1>"
                         case 'disassociate' :
                             if (isGroupRelationship(activity)){
                                 activity.description += activity.object2 + BuildAnchor(activity.summary_fields.group[1], activity.object2, activity) +
                                     'from ' + activity.object1 + BuildAnchor(activity.summary_fields.group[0], activity.object1, activity);
                             }
                             else {
                               if (activity.object1 === 'workflow_job_template_node' && activity.object2 === 'workflow_job_template_node') {
                                  activity.description += 'two nodes on workflow' + BuildAnchor(activity.summary_fields[activity.object1[0]], activity.object1, activity);
                                } else {
                                  activity.description += activity.object2 + BuildAnchor(activity.summary_fields[activity.object2][0], activity.object2, activity) +
                                       'from ' + activity.object1 + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity);
                                }
                             }
                             break;
                         // expected outcome "associated <object2> to <object1>"
                         case 'associate':
                             // groups are the only resource that can be associated/disassociated into each other
                             if (isGroupRelationship(activity)){
                                 activity.description += activity.object1 + BuildAnchor(activity.summary_fields.group[0], activity.object1, activity) +
                                     'to ' + activity.object2 + BuildAnchor(activity.summary_fields.group[1], activity.object2, activity);
                             }
                             else {
                                 if (activity.object1 === 'workflow_job_template_node' && activity.object2 === 'workflow_job_template_node') {
                                   activity.description += 'two nodes on workflow' + BuildAnchor(activity.summary_fields[activity.object1[0]], activity.object1, activity);
                                 } else {
                                   activity.description += activity.object1 + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity) +
                                       'to ' + activity.object2 + BuildAnchor(activity.summary_fields[activity.object2][0], activity.object2, activity);
                                 }
                             }
                             break;
                         case 'delete':
                             activity.description += activity.object1 + BuildAnchor(activity.changes, activity.object1, activity);
                             break;
                         // expected outcome: "operation <object1>"
                         case 'update':
                             activity.description += activity.object1 + BuildAnchor(activity.summary_fields[activity.object1][0], activity.object1, activity);
                             break;
                         case 'create':
                             activity.description += activity.object1 + BuildAnchor(activity.changes, activity.object1, activity);
                             break;
                     }
                     break;
             }
         }
         catch(err){
             $log.debug(err);
             activity.description = i18n._('Event summary not available');
         }
     };
 }

BuildDescription.$inject = ['BuildAnchor', '$log', 'i18n'];
