module.exports = {
    vendor: { 
        files: [
            {
                expand: true,
                src: 'static/css/app.vendor.css',
                dest: '.',
                ext: '.vendor.css'
            }
        ]
    },
    source: { 
        files: [
            {
                expand: true,
                src: 'static/css/app.css',
                dest: '.',
                ext: '.css'
            }
        ]
    }
};
