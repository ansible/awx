export default function BuildAnchor($log, $filter) {
     // Returns a full <a href=''>resource_name</a> HTML string if link can be derived from supplied context
     // returns name of resource if activity stream object doesn't contain enough data to build a UI url
     // arguments are: a summary_field object, a resource type, an activity stream object
     return function (obj, resource, activity) {
         var url = '/#/';
         // try/except pattern asserts that:
         // if we encounter a case where a UI url can't or shouldn't be generated, just supply the name of the resource
         try {
             // catch-all case to avoid generating urls if a resource has been deleted
             // if a resource still exists, it'll be serialized in the activity's summary_fields
             if (!activity.summary_fields[resource]){
                 throw {name : 'ResourceDeleted', message: 'The referenced resource no longer exists'};
             }
             switch (resource) {
                 case 'custom_inventory_script':
                     url += 'inventory_scripts/' + obj.id + '/';
                     break;
                 case 'group':
                     if (activity.operation === 'create' || activity.operation === 'delete'){
                         // the API formats the changes.inventory field as str 'myInventoryName-PrimaryKey'
                         var inventory_id = _.last(activity.changes.inventory.split('-'));
                         url += 'inventories/' + inventory_id + '/groups/edit/' + activity.changes.id;
                     }
                     else {
                         url += 'inventories/' + activity.summary_fields.inventory[0].id + '/groups/edit/' + (activity.changes.id || activity.changes.object1_pk);
                     }
                     break;
                 case 'host':
                     url += 'hosts/' + obj.id;
                     break;
                 case 'job':
                     url += 'jobs/' + obj.id;
                     break;
                 case 'inventory':
                     url += 'inventories/' + obj.id + '/';
                     break;
                 case 'schedule':
                     // schedule urls depend on the resource they're associated with
                     if (activity.summary_fields.job_template){
                         url += 'job_templates/' + activity.summary_fields.job_template.id + '/schedules/' + obj.id;
                     }
                     else if (activity.summary_fields.project){
                         url += 'projects/' + activity.summary_fields.project.id + '/schedules/' + obj.id;
                     }
                     else if (activity.summary_fields.system_job_template){
                         url += 'management_jobs/' + activity.summary_fields.system_job_template.id + '/schedules/edit/' + obj.id;
                     }
                     // urls for inventory sync schedules currently depend on having an inventory id and group id
                     else {
                         throw {name : 'NotImplementedError', message : 'activity.summary_fields to build this url not implemented yet'};
                     }
                     break;
                 case 'notification_template':
                     url += `notification_templates/${obj.id}`;
                     break;
                 case 'role':
                     throw {name : 'NotImplementedError', message : 'role object management is not consolidated to a single UI view'};
                 case 'job_template':
                     url += `templates/job_template/${obj.id}`;
                     break;
                 case 'workflow_job_template':
                     url += `templates/workflow_job_template/${obj.id}`;
                     break;
                 default:
                     url += resource + 's/' + obj.id + '/';
             }
             return ' <a href=\"' + url + '\"> ' + $filter('sanitize')(obj.name || obj.username) + ' </a> ';
         }
         catch(err){
             $log.debug(err);
             return ' ' + $filter('sanitize')(obj.name || obj.username || '') + ' ';
         }
     };
}

 BuildAnchor.$inject = ['$log', '$filter'];
