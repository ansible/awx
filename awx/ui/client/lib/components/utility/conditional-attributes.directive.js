let compileLoopControl = 0;

function conditionalAttributes ($compile) {
    return {
        priority: 100,
        terminal: true,
        compile: () => ({
            pre: (scope, element, attr) => {
                const directives = scope.$eval(attr.conditionalAttributes);
                compileLoopControl++;
                if (compileLoopControl >= 10) {
                    return;
                }
                Object.keys(directives).forEach((key) => {
                    if (directives[key]) {
                        attr.$set(key, true);
                    } else {
                        attr.$set(key, null);
                    }
                });
                attr.$set('conditionalAttributes', null);
                $compile(element)(scope);
                compileLoopControl = 0;
            }
        })
    };
}
conditionalAttributes.$inject = ['$compile'];
export default conditionalAttributes;
