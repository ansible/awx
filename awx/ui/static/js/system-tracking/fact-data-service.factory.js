import fakeData from './fake-data';

function getComparisonData(module) {

    var valueName, leftValue, rightValue;

    switch(module) {
        case 'packages':
            valueName = 'bash';
            leftValue = '5.2.3';
            rightValue = '5.2.4';
            break;
        case 'services':
            valueName = 'httpd';
            leftValue = 'started';
            rightValue = 'absent';
            break;
        case 'files':
            valueName = '/etc/sudoers';
            leftValue = 'some string';
            rightValue = 'some other string';
            break;
        case 'ansible':
            valueName = 'ansible_ipv4_address';
            leftValue = '192.168.0.1';
            rightValue = '192.168.0.2';
            break;
    }

    return [{   module: module,
                valueName: valueName,
                leftValue: leftValue,
                rightValue: rightValue
           }];
}

export default
    ['$q', 'compareHosts', function factDataServiceFactory($q, compareHosts) {
        return function(type) {
            if (type === 'multiHost') {
                return  {   get: function(inventoryId, module, host1, host2) {
                    var result = {};
                    result.leftFilterValue = host1;
                    result.rightFilterValue = host2;

                    result.factComparisonData = compareHosts(module, fakeData.host1, fakeData.host2);

                    return result;
                }
                };
            } else if (type === 'singleHost') {
                return  {   get: function(inventoryId, module, startDate, endDate) {
                    var result = {};
                    result.leftFilterValue = startDate;
                    result.rightFilterValue = endDate;

                    result.factComparisonData = getComparisonData(module);
                    return result;
                }
                };
            }
        };
    }]
