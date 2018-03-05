function conditionalAttributesLink(scope, el, attrs, controller) {
    console.log(scope);
}

let compileLoopControl = 0;

function conditionalAttributes($compile) {
    return {
        priority: 100,
        terminal: true,
        compile: function () {
            return {
                pre: function (scope, element, attr) {
                    let directives = scope.$eval(attr.conditionalAttributes);
                    compileLoopControl++;

                    if (compileLoopControl >= 10) {
                        return;
                    }

                    for (var key in directives) {
                        if (directives.hasOwnProperty(key)) {
                            if (directives[key]) {
                                attr.$set(key, true);
                            } else {
                                attr.$set(key, null);
                            }
                        }
                    }

                    attr.$set('conditionalAttributes', null);
                    $compile(element)(scope);
                    compileLoopControl = 0;

                }
            }
        }
    };
}

conditionalAttributes.$inject = ['$compile']

export default conditionalAttributes;
