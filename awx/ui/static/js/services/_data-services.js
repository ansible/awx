import JobStatusGraphData from 'tower/services/job-status-graph-data';
import HostCountGraphData from 'tower/services/host-count-graph-data';

export default
    angular.module('DataServices', ['ApiLoader'])
        .service('jobStatusGraphData', JobStatusGraphData)
        .service('hostCountGraphData', HostCountGraphData);
