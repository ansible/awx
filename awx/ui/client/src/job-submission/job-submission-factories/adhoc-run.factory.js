/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name helpers.function:Adhoc
 * @description These routines are shared by adhoc command related controllers.
 * The content here is very similar to the JobSubmission helper, and in fact,
 * certain services are pulled from that helper.  This leads to an important
 * point: if you need to create functionality that is shared between the command
 * and playbook run process, put that code in the JobSubmission helper and make
 * it into a reusable step (by specifying a callback parameter in the factory).
 * For a good example of this, please see how the AdhocLaunch factory in this
 * file utilizes the CheckPasswords factory from the JobSubmission helper.
 *
 * #AdhocRelaunch Step 1: preparing the GET to ad_hoc_commands/n/relaunch
 * The adhoc relaunch process is called from the JobSubmission helper.  It is a
 * separate process from the initial adhoc run becuase of the way the API
 * endpoints work.  For AdhocRelaunch, we have access to the original run and
 * we can pull the related relaunch URL by knowing the original Adhoc runs ID.
 *
 * #AdhocRelaunch Step 2: If we got passwords back, add them
 * The relaunch URL gives us back the passwords we need to prompt for (if any).
 * We'll go to step 3 if there are passwords, and step 4 if not.
 *
 * #AdhocRelaunch Step 3: PromptForPasswords and the CreateLaunchDialog
 *
 * #AdhocRelaunch Step 5: StartAdhocRun
 *
 * #AdhocRelaunch Step 6: LaunchJob and navigate to the standard out page.

 * **If you are
 * TODO: once the API endpoint is figured out for running an adhoc command
 * from the form is figured out, the rest work should probably be excised from
 * the controller and moved into here.  See the todo statements in the
 * controller for more information about this.
 */

 export default
     function AdhocRun($location, PromptForPasswords,
         Rest, GetBasePath, ProcessErrors, Wait, Empty, CreateLaunchDialog, $state) {
         return function(params) {
             var id = params.project_id,
                 scope = params.scope.$new(),
                 new_job_id,
                 html,
                 url;

             // this is used to cancel a running adhoc command from
             // the jobs page
             if (scope.removeCancelJob) {
                 scope.removeCancelJob();
             }
             scope.removeCancelJob = scope.$on('CancelJob', function() {
                 // Delete the job
                 Wait('start');
                 Rest.setUrl(GetBasePath('ad_hoc_commands') + new_job_id + '/');
                 Rest.destroy()
                     .then(() => {
                         Wait('stop');
                     })
                     .catch(({data, status}) => {
                         ProcessErrors(scope, data, status,
                           null, { hdr: 'Error!',
                               msg: 'Call to ' + url +
                                   ' failed. DELETE returned status: ' +
                                   status });
                     });
             });

             if (scope.removeStartAdhocRun) {
                 scope.removeStartAdhocRun();
             }

             scope.removeStartAdhocRun = scope.$on('StartAdhocRun', function() {
                 var password,
                     postData={};
                 for (password in scope.passwords) {
                     postData[scope.passwords[password]] = scope[
                         scope.passwords[password]
                     ];
                 }
                 // Re-launch the adhoc job
                 Rest.setUrl(url);
                 Rest.post(postData)
                     .then(({data}) => {
                          Wait('stop');
                          if($location.path().replace(/^\//, '').split('/')[0] !== 'jobs') {
                              $state.go('output', { id: data.id, type: 'command' });
                          }
                     })
                     .catch(({data, status}) => {
                         ProcessErrors(scope, data, status, null, {
                             hdr: 'Error!',
                             msg: 'Failed to launch adhoc command. POST ' +
                                 'returned status: ' + status });
                     });
             });

             //  start routine only if passwords need to be prompted
             if (scope.removeCreateLaunchDialog) {
                 scope.removeCreateLaunchDialog();
             }
             scope.removeCreateLaunchDialog = scope.$on('CreateLaunchDialog',
                 function(e, html, url) {
                     CreateLaunchDialog({
                         scope: scope,
                         html: html,
                         url: url,
                         callback: 'StartAdhocRun'
                     });
                 });

             if (scope.removePromptForPasswords) {
                 scope.removePromptForPasswords();
             }
             scope.removePromptForPasswords = scope.$on('PromptForPasswords',
                 function(e, passwords_needed_to_start,html, url) {
                     PromptForPasswords({
                         scope: scope,
                         passwords: passwords_needed_to_start,
                         callback: 'CreateLaunchDialog',
                         html: html,
                         url: url
                     });
             }); // end password prompting routine

             // start the adhoc relaunch routine
             Wait('start');
             url = GetBasePath('ad_hoc_commands') + id + '/relaunch/';
             Rest.setUrl(url);
             Rest.get()
                 .then(({data}) => {
                     new_job_id = data.id;

                     scope.passwords_needed_to_start = data.passwords_needed_to_start;
                     if (!Empty(data.passwords_needed_to_start) &&
                         data.passwords_needed_to_start.length > 0) {
                         // go through the password prompt routine before
                         // starting the adhoc run
                         scope.$emit('PromptForPasswords', data.passwords_needed_to_start, html, url);
                     }
                     else {
                         // no prompting of passwords needed
                         scope.$emit('StartAdhocRun');
                     }
                 })
                 .catch(({data, status}) => {
                     ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                     msg: 'Failed to get job template details. GET returned status: ' + status });
                 });
         };
     }

 AdhocRun.$inject =
     [   '$location',
         'PromptForPasswords', 'Rest', 'GetBasePath', 'ProcessErrors',
         'Wait', 'Empty', 'CreateLaunchDialog', '$state'
     ];
