import stringFilters from 'tower/shared/string-filters/main';
import formatEpoch from 'tower/shared/format-epoch/main';

var $injector = angular.injector(['ng', stringFilters.name, formatEpoch.name]);
var $interpolate = $injector.get('$interpolate');

function FactTemplate(templateString) {
    this.templateString = templateString;
}

function loadFactTemplate(factTemplate, fact) {
    if (_.isFunction(factTemplate)) {
        return factTemplate(fact);
    } else {
        return factTemplate;
    }
}

FactTemplate.prototype.render = function(factData) {

    if (_.isUndefined(factData) || _.isEmpty(factData)) {
        return 'absent';
    }

    var template = loadFactTemplate(this.templateString, factData);
    return $interpolate(template)(factData);
};

FactTemplate.prototype.hasTemplate = function() {
    return !_.isUndefined(this.templateString);
};

export default FactTemplate;
