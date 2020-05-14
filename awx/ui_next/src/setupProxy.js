const { createProxyMiddleware } = require('http-proxy-middleware');

const TARGET_PORT = process.env.TARGET_PORT || 8043;
const TARGET_HOST = process.env.TARGET_HOST || 'localhost';
const TARGET = `https://${TARGET_HOST}:${TARGET_PORT}`;

// Note: The websocket proxy is configured
// manually using the 'proxy' field in package.json

module.exports = app => {
  app.use(
    '/api/login/',
    createProxyMiddleware({
      target: TARGET,
      secure: false,
      ws: false,
      headers: {
        Host: `localhost:${TARGET_PORT}`,
        Origin: TARGET,
        Referer: `${TARGET}/`,
      },
    })
  );
  app.use(
    '/api',
    createProxyMiddleware({
      target: TARGET,
      secure: false,
      ws: false,
      bypass: req =>
        req.originalUrl.includes('hot-update.json') ||
        req.originalUrl.includes('login'),
    })
  );
};
