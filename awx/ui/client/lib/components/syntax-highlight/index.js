import syntaxHighlight from './syntax-highlight.directive';

const MODULE_NAME = 'at.syntax.highlight';

angular.module(MODULE_NAME, [])
    .directive('atSyntaxHighlight', syntaxHighlight);

export default MODULE_NAME;
