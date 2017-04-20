module.exports = {
    extends: 'airbnb-base',
    plugins: [
        'import'
    ],
    env: {
        browser: true,
        node: true
    },
    globals: {
        angular: true,  
        d3: true,
        $: true,
        codemirror: true,
        jsyaml: true
    },
    rules: {
        indent: [0, 4],
        'comma-dangle': 0,
        'prefer-const': 0,
        'space-before-function-paren': [2, 'always']
    }
};
