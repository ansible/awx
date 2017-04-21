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
        on: false,
        button: {
            text: 'Key'
        },
        body: {
            text: 'Yadda yadda yadda'
        }
    };
}

// IndexController.$inject = [];

export default IndexController;
