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
             let name;
             switch (resource) {
                 case 'custom_inventory_script':
                     url += 'inventory_scripts/' + obj.id + '/';
                     break;
                 case 'group':
                     if (activity.operation === 'create' || activity.operation === 'delete'){
                         // the API formats the changes.inventory field as str 'myInventoryName-PrimaryKey'
                         var inventory_id = _.last(activity.changes.inventory.split('-'));
                         url += 'inventories/inventory/' + inventory_id + '/groups/edit/' + activity.changes.id;
                     }
                     else {
                         url += 'inventories/inventory/' + activity.summary_fields.inventory[0].id + '/groups/edit/' + (activity.changes.id || activity.changes.object1_pk);
                     }
                     break;
                 case 'host':
                     url += 'hosts/' + obj.id;
                     break;
                 case 'job':
                     url += 'jobs/' + obj.id;
                     break;
                 case 'inventory':
                     url += obj.kind && obj.kind === "smart" ? 'inventories/smart/' + obj.id + '/' : 'inventories/inventory/' + obj.id + '/';
                     break;
                 case 'schedule':
                     // schedule urls depend on the resource they're associated with
                     if (activity.summary_fields.job_template){
                         url += 'templates/job_template/' + activity.summary_fields.job_template[0].id + '/schedules/' + obj.id;
                     }
                     else if (activity.summary_fields.project){
                         url += 'projects/' + activity.summary_fields.project[0].id + '/schedules/' + obj.id;
                     }
                     else if (activity.summary_fields.system_job_template){
                         url += 'management_jobs/management_jobs/' + activity.summary_fields.system_job_template[0].id + '/schedules/edit/' + obj.id;
                     }
                     // urls for inventory sync schedules currently depend on having an inventory id and group id
                     else {
                         throw {name : 'NotImplementedError', message : 'activity.summary_fields to build this url not implemented yet'};
                     }
                     break;
                case 'setting':
                    if (activity.summary_fields.setting[0].category === 'jobs' ||
                        activity.summary_fields.setting[0].category === 'ui') {
                        url += `settings/${activity.summary_fields.setting[0].category}`;
                    }
                    else if (activity.summary_fields.setting[0].category === 'system' ||
                        activity.summary_fields.setting[0].category === 'logging') {
                        url += `settings/system`;
                    }
                    else {
                        url += `settings/auth`;
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
                 case 'workflow_job_template_node':
                     url += `templates/workflow_job_template/${activity.summary_fields.workflow_job_template[0].id}`;
                     name = activity.summary_fields.workflow_job_template[0].name;
                     break;
                 case 'workflow_job':
                     url += `workflows/${obj.id}`;
                     break;
                 case 'label':
                     url = null;
                     break;
                 case 'inventory_source':
                     const inventoryId = _.get(obj, 'inventory', '').split('-').reverse()[0];
                     url += `inventories/inventory/${inventoryId}/inventory_sources/edit/${obj.id}`;
                     break;
                 case 'o_auth2_application':
                     url += `applications/${obj.id}`;
                     break;
                 case 'workflow_approval':
                     url += `workflows/${activity.summary_fields.workflow_job[0].id}`;
                     name = activity.summary_fields.workflow_job[0].name + ' | ' + activity.summary_fields.workflow_approval[0].name;
                     break;
                 case 'workflow_approval_template':
                     url += `templates/workflow_job_template/${activity.summary_fields.workflow_job_template[0].id}/workflow-maker`;
                     name = activity.summary_fields.workflow_job_template[0].name + ' | ' + activity.summary_fields.workflow_approval_template[0].name;
                     break;
                 default:
                     url += resource + 's/' + obj.id + '/';
             }

             name = $filter('sanitize')(name || obj.name || obj.username);

             if (url) {
                return ` <a href=\"${url}\">&nbsp;${name}&nbsp;</a> `;
             }

             return ` <span>&nbsp;${name}&nbsp;</span> `;
         }
         catch(err){
             $log.debug(err);
             return ' ' + $filter('sanitize')(obj.name || obj.username || '') + ' ';
         }
     };
}

 BuildAnchor.$inject = ['$log', '$filter'];
