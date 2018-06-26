const API_PAGE_SIZE = 200;
const PAGE_SIZE = 50;
const ORDER_BY = 'counter';

const BASE_PARAMS = {
    page_size: PAGE_SIZE,
    order_by: ORDER_BY,
};

const merge = (...objs) => _.merge({}, ...objs);

function JobEventsApiService ($http, $q) {
    this.init = (endpoint, params) => {
        this.endpoint = endpoint;
        this.params = merge(BASE_PARAMS, params);

        this.state = { count: 0, maxCounter: 0 };
        this.cache = {};
    };

    this.clearCache = () => {
        Object.keys(this.cache).forEach(key => {
            delete this.cache[key];
        });
    };

    this.fetch = () => this.getLast()
        .then(results => {
            this.cache.last = results;

            return this;
        });

    this.getFirst = () => {
        const page = 1;
        const params = merge(this.params, { page });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;
                const maxCounter = Math.max(...results.map(({ counter }) => counter));

                this.state.count = count;

                if (maxCounter > this.state.maxCounter) {
                    this.state.maxCounter = maxCounter;
                }

                return results;
            });
    };

    this.getPage = number => {
        if (number < 1 || number > this.getLastPageNumber()) {
            return $q.resolve([]);
        }

        const params = merge(this.params, { page: number });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;
                const maxCounter = Math.max(...results.map(({ counter }) => counter));

                this.state.count = count;

                if (maxCounter > this.state.maxCounter) {
                    this.state.maxCounter = maxCounter;
                }

                return results;
            });
    };

    this.getLast = () => {
        if (this.cache.last) {
            return $q.resolve(this.cache.last);
        }

        const params = merge(this.params, { page: 1, order_by: `-${ORDER_BY}` });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;
                const maxCounter = Math.max(...results.map(({ counter }) => counter));

                let rotated = results;

                if (count > PAGE_SIZE) {
                    rotated = results.splice(count % PAGE_SIZE);

                    if (results.length > 0) {
                        rotated = results;
                    }
                }

                this.state.count = count;

                if (maxCounter > this.state.maxCounter) {
                    this.state.maxCounter = maxCounter;
                }

                return rotated;
            });
    };

    this.getRange = range => {
        if (!range) {
            return $q.resolve([]);
        }

        const [low, high] = range;
        const params = merge(this.params, { counter__gte: [low], counter__lte: [high] });

        params.page_size = API_PAGE_SIZE;

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results } = data;
                const maxCounter = Math.max(...results.map(({ counter }) => counter));

                if (maxCounter > this.state.maxCounter) {
                    this.state.maxCounter = maxCounter;
                }

                return results;
            });
    };

    this.getLastPageNumber = () => Math.ceil(this.state.count / PAGE_SIZE);
    this.getMaxCounter = () => this.state.maxCounter;
}

JobEventsApiService.$inject = ['$http', '$q'];

export default JobEventsApiService;
