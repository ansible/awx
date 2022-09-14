const { createProxyMiddleware } = require('http-proxy-middleware');

const TARGET = process.env.TARGET || 'https://localhost:8043';

module.exports = (app) => {
  app.use(
    createProxyMiddleware(['/api', '/websocket', '/sso'], {
      target: TARGET,
      secure: false,
      ws: true,
      changeOrigin: true,
    })
  );
};
