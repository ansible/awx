export function formatFactForDisplay(fact, renderOptions) {

    var factTemplate = renderOptions.factTemplate;

    var template = factTemplate;

    // if (!renderOptions.supportsValueArray) {
    //     comparatorFact = comparatorFact[0];
    // }

    return template.render(fact);

}
