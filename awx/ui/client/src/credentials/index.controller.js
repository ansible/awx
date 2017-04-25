function IndexController () {
    let vm = this;

    vm.panel = {
        heading: {
            title: {
                text: 'Credentials'
            },
            badge: {
                text: 5
            }
        }
    };

    vm.key = {
        id: 'key-group',
        show: false,
        button: {
            text: 'Key'
        },
        content: {
            text: 'Yadda yadda yadda'
        }
    };
}

// IndexController.$inject = [];

export default IndexController;
