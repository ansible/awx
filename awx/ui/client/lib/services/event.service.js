function EventService () {
    this.addListeners = list => {
        let listeners = [];

        list.forEach(args => listeners.push(this.addListener(...args)));

        return listeners;
    };

    this.addListener = (el, name, fn) => {
        let listener = {
            fn,
            name,
            el
        };

        listener.el.addEventListener(listener.name, listener.fn);

        return listener;
    };

    this.remove = listeners => {
        listeners.forEach(listener => {
            listener.el.removeEventListener(listener.name, listener.fn);
        });
    };
}

export default EventService;
