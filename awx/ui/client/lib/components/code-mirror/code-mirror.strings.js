function CodeMirrorStrings (BaseString) {
    BaseString.call(this, 'code_mirror');

    const { t } = this;
    const ns = this.code_mirror;

    ns.CLOSE_MODAL = t.s('Close variables modal');

    ns.label = {
        EXTRA_VARIABLES: t.s('EXTRA VARIABLES'),
        VARIABLES: t.s('VARIABLES'),
        EXPAND: t.s('EXPAND'),
        YAML: t.s('YAML'),
        JSON: t.s('JSON'),
        READONLY: t.s('READ ONLY')
    };

    ns.tooltip = {
        TOOLTIP: t.s(`
            <p>
                Enter inventory variables using either JSON or YAML
                syntax. Use the radio button to toggle between the two.
            </p>
                JSON:
            <br/>
            <blockquote>
            {
                <br/>"somevar": "somevalue",
                <br/>"password": "magic"
                <br/>
            }
            </blockquote>
                YAML:
            <br/>
            <blockquote>
                ---
                <br/>somevar: somevalue
                <br/>password: magic
                <br/>
            </blockquote>
            <p>
                View JSON examples at
                <a href="http://www.json.org" target="_blank">www.json.org</a>
            </p>
            <p>
                View YAML examples at
                <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">
                docs.ansible.com</a>
            </p>`),
        TOOLTIP_TITLE: t.s('EXTRA VARIABLES'),
        JOB_RESULTS: t.s('Read-only view of extra variables added to the job template.')
    };
}

CodeMirrorStrings.$inject = ['BaseStringService'];

export default CodeMirrorStrings;
