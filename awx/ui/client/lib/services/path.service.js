function getPartialPath (path) {
    return `/static/partials/${path}.partial.html`;
}

function getViewPath (path) {
    return `/static/views/${path}.view.html`;
}

function PathService () {
    return {
        getPartialPath,
        getViewPath
    };
}

export default PathService;
