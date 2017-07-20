module.exports = {
    vendor: { 
        files: [
            {
                expand: true,
                src: 'static/css/tower.vendor.css',
                dest: '.',
                ext: '.vendor.min.css'
            }
        ]
    },
    source: { 
        files: [
            {
                expand: true,
                src: 'static/css/tower.css',
                dest: '.',
                ext: '.min.css'
            }
        ]
    }
};
