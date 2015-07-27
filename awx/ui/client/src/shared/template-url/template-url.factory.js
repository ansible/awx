// This function is accessible outside of angular
//
export function templateUrl(path) {
    return _templateUrl(null, path);
}

function _templateUrl($sce, path, isTrusted) {
    isTrusted = isTrusted !== false; // defaults to true, can be passed in as false
    var parts = ['', 'static'];
    parts.push(path);

    var url = parts.join('/') + '.partial.html';

    if (isTrusted && $sce) {
        url = $sce.trustAsResourceUrl(url);
    }

    return url;
}

export default
    [   '$sce',
        function($sce) {
            return _.partial(_templateUrl, $sce);
        }
    ];
