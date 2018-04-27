import codemirror from './code-mirror.directive';
import modal from './modal/code-mirror-modal.directive';
import strings from './code-mirror.strings';

const MODULE_NAME = 'at.code.mirror';

angular.module(MODULE_NAME, [])
    .directive('atCodeMirror', codemirror)
    .directive('atCodeMirrorModal', modal)
    .service('CodeMirrorStrings', strings);

export default MODULE_NAME;
