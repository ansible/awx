function CacheService ($cacheFactory, $q) {
    let cache = $cacheFactory('api');

    this.put = (key, data) => {
        return cache.put(key, data); 
    };

    this.get = (key) => {
        return $q.resolve(cache.get(key));
    };

    this.remove = (key) => {
        if (!key) { 
            return cache.removeAll();
        }

        return cache.remove(key);
    };

    this.createKey = (method, path, resource) => {
        let key = `${method.toUpperCase()}.${path}`;

        if (resource) {
            if (resource.id) {
                key += `${resource.id}/`;
            } else if (Number(resource)) {
                key += `${resource}/`;
            }
        }

        return key;
    }
}

CacheService.$inject = ['$cacheFactory', '$q'];

export default CacheService;
