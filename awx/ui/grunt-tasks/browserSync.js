var django_port = process.env.npm_package_config_django_port,
    django_host = process.env.npm_package_config_django_host;

module.exports = {
    http: {
        bsFiles: {
            src: [
                'static/**/*',
                '!static/tower.vendor.js',
                '!static/tower.vendor.map.js',
                '!static/tower.js.map'
            ]
        },
        options: {
            proxy: {
                target: `${django_host}:${django_port}`,
                ws: true
            },
            keepalive: false,
            watchTask: true,
            // The browser-sync-client lib will write your current scroll position to window.name
            // https://github.com/BrowserSync/browser-sync-client/blob/a2718faa91e11553feca7a3962313bf1ec6ba3e5/dist/index.js#L500
            // This strategy is enabled in the core browser-sync lib, and not externally documented as an option. Yay!
            // https://github.com/BrowserSync/browser-sync/blob/a522aaf12b6167d5591ed285eb3086f43a4d9ac2/lib/default-config.js#L312
            scrollRestoreTechnique: null,
            injectChanges: true
        }
    }
};
