import TemplatesStrings from './templates.strings';

const MODULE_NAME = 'at.features.templates';

angular
    .module(MODULE_NAME, [])
    .service('TemplatesStrings', TemplatesStrings);

export default MODULE_NAME;
