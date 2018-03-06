import TemplatesStrings from './templates.strings';
import TemplatesListController from './list-templates.controller';

const MODULE_NAME = 'at.features.templates';

angular
    .module(MODULE_NAME, [])
    .controller('TemplatesListController', TemplatesListController)
    .service('TemplatesStrings', TemplatesStrings);

export default MODULE_NAME;
