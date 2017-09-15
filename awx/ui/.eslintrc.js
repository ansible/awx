const path = require('path');

module.exports = {
    extends: [
        'airbnb-base'
    ],
    plugins: [
        'import'
    ],
    settings: {
        'import/resolver': {
            webpack: {
                config: path.join(__dirname, 'build/webpack.development.js')
            }
        }
    },
    env: {
        browser: true,
        node: true
    },
    globals: {
        angular: true,  
        d3: true,
        $: true,
        _: true,
        codemirror: true,
        jsyaml: true
    },
    rules: {
        indent: [0, 4],
        'comma-dangle': 0,
        'space-before-function-paren': [2, 'always'],
        'arrow-parens': 0,
        'no-param-reassign': 0,
        'no-underscore-dangle': 0,
        'no-mixed-operators': 0,
        'no-plusplus': 0,
        'no-continue': 0,
        'object-curly-newline': 0
    }
};
