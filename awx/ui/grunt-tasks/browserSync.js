var django_port = process.env.npm_package_config_django_port,
    django_host = process.env.npm_package_config_django_host;

module.exports = {
    http: {
        bsFiles: {
            src: [
                'static/**/*'
            ]
        },
        options: {
            proxy: {
                target: `${django_host}:${django_port}`,
                ws: true
            },
            keepalive: false,
            watchTask: true
        }
    }
};
