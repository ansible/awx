const path = require('path');

const _ = require('lodash');

const ESLINTRC_PATH = path.resolve(__dirname, '..', '.eslintrc.js');
const LINTED_PATHS = [
    /.js$/
];

let base = require('./webpack.base');

let development = {
    devtool: 'cheap-source-map',
    module: {
        rules: [
            {
                test: /\.js$/,
                enforce: 'pre',
                exclude: /node_modules/,
                loader: 'eslint-loader'
            }
        ]
    }
};

development.module.rules = base.module.rules.concat(development.module.rules)

module.exports = _.merge(base, development);
