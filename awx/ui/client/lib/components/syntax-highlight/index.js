// import 'codemirror/mode/jinja2/jinja2';
import syntaxHighlight from './syntax-highlight.directive';
// import strings from './syntax-highlight.strings';

const MODULE_NAME = 'at.syntax.highlight';

angular.module(MODULE_NAME, [])
    .directive('atSyntaxHighlight', syntaxHighlight);

export default MODULE_NAME;
