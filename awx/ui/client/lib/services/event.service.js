function EventService () {
    this.addListeners = list => {
        const listeners = [];

        list.forEach(args => listeners.push(this.addListener(...args)));

        return listeners;
    };

    this.addListener = (el, name, fn) => {
        const listener = {
            fn,
            name,
            el
        };

        if (Array.isArray(name)) {
            name.forEach(e => listener.el.addEventListener(e, listener.fn));
        } else {
            listener.el.addEventListener(listener.name, listener.fn);
        }

        return listener;
    };

    this.remove = listeners => {
        listeners.forEach(listener => {
            if (Array.isArray(listener.name)) {
                listener.name.forEach(name => listener.el.removeEventListener(name, listener.fn));
            } else {
                listener.el.removeEventListener(listener.name, listener.fn);
            }
        });
    };
}

export default EventService;
