const path = require('path');

const _ = require('lodash');

let base = require('./webpack.base');

let development = {
    devtool: 'cheap-source-map'
};

module.exports = _.merge(base, development);
