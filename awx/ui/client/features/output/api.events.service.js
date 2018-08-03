import {
    API_MAX_PAGE_SIZE,
    OUTPUT_ORDER_BY,
    OUTPUT_PAGE_SIZE,
} from './constants';

const BASE_PARAMS = {
    page_size: OUTPUT_PAGE_SIZE,
    order_by: OUTPUT_ORDER_BY,
};

const merge = (...objs) => _.merge({}, ...objs);

function JobEventsApiService ($http, $q) {
    this.init = (endpoint, params) => {
        this.endpoint = endpoint;
        this.params = merge(BASE_PARAMS, params);

        this.state = { count: 0, maxCounter: 0 };
        this.cache = {};
    };

    this.fetch = () => this.getLast()
        .then(results => {
            this.cache.last = results;

            return this;
        });

    this.clearCache = () => {
        Object.keys(this.cache).forEach(key => {
            delete this.cache[key];
        });
    };

    this.pushMaxCounter = events => {
        const maxCounter = Math.max(...events.map(({ counter }) => counter));

        if (maxCounter > this.state.maxCounter) {
            this.state.maxCounter = maxCounter;
        }

        return maxCounter;
    };

    this.getFirst = () => {
        const params = merge(this.params, { page: 1 });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;

                this.state.count = count;
                this.pushMaxCounter(results);

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

                this.state.count = count;
                this.pushMaxCounter(results);

                return results;
            });
    };

    this.getLast = () => {
        if (this.cache.last) {
            return $q.resolve(this.cache.last);
        }

        const params = merge(this.params, { page: 1, order_by: `-${OUTPUT_ORDER_BY}` });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;

                let rotated = results;

                if (count > OUTPUT_PAGE_SIZE) {
                    rotated = results.splice(count % OUTPUT_PAGE_SIZE);

                    if (results.length > 0) {
                        rotated = results;
                    }
                }

                this.state.count = count;
                this.pushMaxCounter(results);

                return rotated;
            });
    };

    this.getRange = range => {
        if (!range) {
            return $q.resolve([]);
        }

        const [low, high] = range;

        if (low > high) {
            return $q.resolve([]);
        }

        const params = merge(this.params, { counter__gte: [low], counter__lte: [high] });

        params.page_size = API_MAX_PAGE_SIZE;

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results } = data;

                this.pushMaxCounter(results);

                return results;
            });
    };

    this.getLastPageNumber = () => Math.ceil(this.state.count / OUTPUT_PAGE_SIZE);
    this.getMaxCounter = () => this.state.maxCounter;
}

JobEventsApiService.$inject = ['$http', '$q'];

export default JobEventsApiService;
