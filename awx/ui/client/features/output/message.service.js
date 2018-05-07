function MessageService () {
    const listeners = {};
    const registry = {};

    this.subscribe = (key, listener) => {
        registry[key] = registry[key] || 0;

        listeners[key] = listeners[key] || {};
        listeners[key][registry[key]] = listener;

        const unsubscribe = this.createCallback(key, registry[key]);

        registry[key]++;

        return unsubscribe;
    };

    this.dispatch = (key, data) => {
        if (!listeners[key]) {
            return;
        }

        const indices = Object.keys(listeners[key]);

        for (let i = 0; i < indices.length; i++) {
            listeners[key][indices[i]](data);
        }
    };

    this.createCallback = (key, index) => {
        const callback = () => {
            if (listeners[key]) {
                delete listeners[key][index];
            }
        };

        return callback;
    };
}

export default MessageService;
