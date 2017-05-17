function PathService () {
    this.getPartialPath = path => {
        return `/static/partials/${path}.partial.html`;
    };

    this.getViewPath = path => {
        return `/static/views/${path}.view.html`;
    }
}

export default PathService;
