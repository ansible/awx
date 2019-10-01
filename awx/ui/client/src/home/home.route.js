import {templateUrl} from '../shared/template-url/template-url.factory';
import controller from './home.controller';
import { N_ } from '../i18n';

export default {
    name: 'dashboard',
    url: '/home',
    templateUrl: templateUrl('home/home'),
    controller: controller,
    params: { licenseMissing: null },
    data: {
        activityStream: true,
        refreshButton: true
    },
    ncyBreadcrumb: {
        label: N_("DASHBOARD")
    },
    resolve: {
        graphData: ['$q', 'jobStatusGraphData', '$rootScope',
            function($q, jobStatusGraphData, $rootScope) {
                return $rootScope.basePathsLoaded.promise.then(function() {
                    return $q.all({
                        jobStatus: jobStatusGraphData.get("month", "all"),
                    });
                });
            }
        ]
    }
    // name: 'setup.about',
    // route: '/about',
    // controller: controller,
    // ncyBreadcrumb: {
    //     label: N_("ABOUT")
    // },
    // onExit: function(){
    //     // hacky way to handle user browsing away via URL bar
    //     $('.modal-backdrop').remove();
    //     $('body').removeClass('modal-open');
    // },
    // templateUrl: templateUrl('about/about')
};
