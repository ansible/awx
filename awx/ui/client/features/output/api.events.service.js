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

        this.state = { current: 0, count: 0 };
    };

    this.fetch = () => this.getLast().then(() => this);

    this.getFirst = () => {
        const page = 1;
        const params = merge(this.params, { page });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results, count } = data;

                this.state.count = count;
                this.state.current = page;

                return results;
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
                const maxCounter = Math.max(results.map(({ counter }) => counter));

                this.state.current = Math.ceil(maxCounter / PAGE_SIZE);

                return results;
            });
    };

    this.getLast = () => {
        const params = merge(this.params, { page: 1, order_by: `-${ORDER_BY}` });

        return $http.get(this.endpoint, { params })
            .then(({ data }) => {
                const { results } = data;
                const count = Math.max(...results.map(({ counter }) => counter));

                let rotated = results;

                if (count > PAGE_SIZE) {
                    rotated = results.splice(count % PAGE_SIZE);

                    if (results.length > 0) {
                        rotated = results;
                    }
                }
                this.state.count = count;
                this.state.current = Math.ceil(count / PAGE_SIZE);

                return rotated;
            });
    };

    this.getCurrentPageNumber = () => this.state.current;
    this.getLastPageNumber = () => Math.ceil(this.state.count / PAGE_SIZE);
    this.getPreviousPageNumber = () => Math.max(1, this.state.current - 1);
    this.getNextPageNumber = () => Math.min(this.state.current + 1, this.getLastPageNumber());
    this.getMaxCounter = () => this.state.count;

    this.getNext = () => this.getPage(this.getNextPageNumber());
    this.getPrevious = () => this.getPage(this.getPreviousPageNumber());
}

JobEventsApiService.$inject = ['$http', '$q'];

export default JobEventsApiService;
