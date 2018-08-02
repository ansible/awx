import ProjectsStrings from './projects.strings';

const MODULE_NAME = 'at.features.projects';

angular
    .module(MODULE_NAME, [])
    .service('ProjectsStrings', ProjectsStrings);

export default MODULE_NAME;
