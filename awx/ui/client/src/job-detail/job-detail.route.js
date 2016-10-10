<<<<<<< 4cf6a946a1aa14b7d64a8e1e8dabecfd3d056f27
//<<<<<<< bc59236851902d7c768aa26abdb7dc9c9dc27a5a
/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// <<<<<<< a3d9eea2c9ddb4e16deec9ec38dea16bf37c559d
// import { templateUrl } from '../shared/template-url/template-url.factory';
//
// export default {
//     name: 'jobDetail',
//     url: '/jobs/{id: int}',
//     ncyBreadcrumb: {
//         parent: 'jobs',
//         label: "{{ job.id }} - {{ job.name }}"
//     },
//     data: {
//         socket: {
//             "groups": {
//                 "jobs": ["status_changed", "summary"],
//                 "job_events": []
//             }
//         }
//     },
//     templateUrl: templateUrl('job-detail/job-detail'),
//     controller: 'JobDetailController'
// };
// =======
// import {templateUrl} from '../shared/template-url/template-url.factory';
//
// export default {
//     name: 'jobDetail',
//     url: '/jobs/:id',
//     ncyBreadcrumb: {
//         parent: 'jobs',
//         label: "{{ job.id }} - {{ job.name }}"
//     },
//     socket: {
//         "groups":{
//             "jobs": ["status_changed", "summary"],
//             "job_events": []
//         }
//     },
//     templateUrl: templateUrl('job-detail/job-detail'),
//     controller: 'JobDetailController'
// };
//=======
=======
>>>>>>> Rebase of devel (w/ channels) + socket rework for new job details
// /*************************************************
//  * Copyright (c) 2016 Ansible, Inc.
//  *
//  * All Rights Reserved
//  *************************************************/
//
// import {templateUrl} from '../shared/template-url/template-url.factory';
//
// export default {
//     name: 'jobDetail',
//     url: '/jobs/:id',
//     ncyBreadcrumb: {
//         parent: 'jobs',
//         label: "{{ job.id }} - {{ job.name }}"
//     },
//     socket: {
//         "groups":{
//             "jobs": ["status_changed", "summary"],
//             "job_events": []
//         }
//     },
//     resolve: {
//         jobEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
//             if (!$rootScope.event_socket) {
//                 $rootScope.event_socket = Socket({
//                     scope: $rootScope,
//                     endpoint: "job_events"
//                 });
//                 $rootScope.event_socket.init();
//                 // returns should really be providing $rootScope.event_socket
//                 // otherwise, we have to inject the entire $rootScope into the controller
//                 return true;
//             } else {
//                 return true;
//             }
//         }]
//     },
//     templateUrl: templateUrl('job-detail/job-detail'),
//     controller: 'JobDetailController'
// };
