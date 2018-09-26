const webpack = require('webpack');

const TARGET_PORT = 8043;
const TARGET = `https://localhost:${TARGET_PORT}`;

module.exports = {
  entry: './src/index.js',
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      }
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx']
  },
  output: {
    path: __dirname + '/dist',
    publicPath: '/',
    filename: 'bundle.js'
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin()
  ],
  devServer: {
    contentBase: './dist',
    hot: true,
    inline: true,
    stats: 'minimal',
    host: '127.0.0.1',
    https: true,
    port: 3000,
    clientLogLevel: 'none',
    proxy: [
    {
        context: '/api/login/',
        target: TARGET,
        secure: false,
        ws: false,
        headers: {
            Host: `localhost:${TARGET_PORT}`,
            Origin: TARGET,
            Referer: `${TARGET}/`
        }
    },
    {
        context: '/api',
        target: TARGET,
        secure: false,
        ws: false,
        bypass: req => (req.originalUrl.includes('hot-update.json') || req.originalUrl.includes('login')),
    },
    {
        context: '/websocket',
        target: TARGET,
        secure: false,
        ws: true
    }]
  }
};
