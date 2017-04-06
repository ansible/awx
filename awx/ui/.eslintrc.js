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
        indent: ['error', 4],
        'comma-dangle': 'off',
        'prefer-const': ['off']
    }
};
