function templateUrl($sce, path, isTrusted) {
    isTrusted = isTrusted !== false; // defaults to true, can be passed in as false
    var parts = ['', 'static', 'js'];
    parts.push(path);

    var url = parts.join('/') + '.partial.html';

    if (isTrusted) {
        url = $sce.trustAsResourceUrl(url);
    }

    return url;
}

export default
    [   '$sce',
        function($sce) {
            return _.partial(templateUrl, $sce);
        }
    ];
