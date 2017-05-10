function addListeners (scope, list) {
    let listeners = [];

    list.forEach(args => {
        listeners.push(addListener.call(null, scope, ...args));
    });

    return listeners;
}

function addListener (scope, el, name, fn, type) {
    type = type || '$apply';

    let listener = {
        fn: () => scope[type](fn),
        name,
        el
    };

    listener.el.addEventListener(listener.name, listener.fn);

    return listener;
}

function remove (listeners) {
    listeners.forEach(listener => {
        listener.el.removeEventListener(listener.name, listener.fn);
    });
}

function EventService () {
    return {
        addListeners,
        remove
    };
}

export default EventService;
