import React, {
  Component,
  Fragment
} from 'react';
import { Title, EmptyState, EmptyStateIcon, EmptyStateBody } from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { I18n, i18nMark } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import DataListToolbar from '../DataListToolbar';
import NotificationListItem from './NotificationListItem';
import Pagination from '../Pagination';

import {
  encodeQueryString,
  parseQueryString,
} from '../../qs';

class Notifications extends Component {
  columns = [
    { name: i18nMark('Name'), key: 'name', isSortable: true },
    { name: i18nMark('Modified'), key: 'modified', isSortable: true, isNumeric: true },
    { name: i18nMark('Created'), key: 'created', isSortable: true, isNumeric: true },
  ];

  defaultParams = {
    page: 1,
    page_size: 5,
    order_by: 'name',
  };

  pageSizeOptions = [5, 10, 25, 50];

  constructor (props) {
    super(props);

    const { page, page_size } = this.getQueryParams();

    this.state = {
      page,
      page_size,
      sortedColumnKey: 'name',
      sortOrder: 'ascending',
      count: null,
      error: null,
      loading: true,
      results: [],
      selected: [],
      successTemplateIds: [],
      errorTemplateIds: []
    };

    this.onSearch = this.onSearch.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
    this.onSort = this.onSort.bind(this);
    this.onSetPage = this.onSetPage.bind(this);
    this.onSelectAll = this.onSelectAll.bind(this);
    this.onSelect = this.onSelect.bind(this);
    this.toggleError = this.toggleError.bind(this);
    this.toggleSuccess = this.toggleSuccess.bind(this);
    this.updateUrl = this.updateUrl.bind(this);
    this.postToError = this.postToError.bind(this);
    this.postToSuccess = this.postToSuccess.bind(this);
    this.fetchNotifications = this.fetchNotifications.bind(this);
  }

  componentDidMount () {
    const queryParams = this.getQueryParams();
    // TODO: remove this hack once tab query param is gone
    const { tab, ...queryParamsWithoutTab } = queryParams;
    this.fetchNotifications(queryParamsWithoutTab);
  }

  onSearch () {
    const { sortedColumnKey, sortOrder } = this.state;

    this.onSort(sortedColumnKey, sortOrder);
  }

  getQueryParams (overrides = {}) {
    const { location } = this.props;
    const { search } = location;

    const searchParams = parseQueryString(search.substring(1));
    // TODO: remove this hack once tab query param is gone
    const { tab, ...queryParamsWithoutTab } = searchParams;

    return Object.assign({}, this.defaultParams, queryParamsWithoutTab, overrides);
  }

  onSort = (sortedColumnKey, sortOrder) => {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ order_by, page_size });

    this.fetchNotifications(queryParams);
  };

  onSetPage = (pageNumber, pageSize) => {
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);

    const queryParams = this.getQueryParams({ page, page_size });

    this.fetchNotifications(queryParams);
  };

  onSelectAll = isSelected => {
    const { results } = this.state;

    const selected = isSelected ? results.map(o => o.id) : [];

    this.setState({ selected });
  };

  onSelect = id => {
    const { selected } = this.state;

    const isSelected = selected.includes(id);

    if (isSelected) {
      this.setState({ selected: selected.filter(s => s !== id) });
    } else {
      this.setState({ selected: selected.concat(id) });
    }
  };

  toggleError = (id, isCurrentlyOn) => {
    this.postToError(id, isCurrentlyOn);
  };

  toggleSuccess = (id, isCurrentlyOn) => {
    this.postToSuccess(id, isCurrentlyOn);
  };

  updateUrl (queryParams) {
    const { history, location, match } = this.props;
    const pathname = match.url;
    const search = `?${encodeQueryString(queryParams)}`;

    if (search !== location.search) {
      history.replace({ pathname, search });
    }
  }

  async postToError (id, isCurrentlyOn) {
    const { postError, match } = this.props;
    const postParams = { id };
    if (isCurrentlyOn) {
      postParams.disassociate = true;
    }
    try {
      await postError(match.params.id, postParams);
    } catch (err) {
      this.setState({ error: true });
    } finally {
      if (isCurrentlyOn) {
        // Remove it from state
        this.setState((prevState) => ({
          errorTemplateIds: prevState.errorTemplateIds.filter((templateId) => templateId !== id)
        }));
      } else {
        // Add it to state
        this.setState(prevState => ({
          errorTemplateIds: [...prevState.errorTemplateIds, id]
        }));
      }
    }
  }

  async postToSuccess (id, isCurrentlyOn) {
    const { postSuccess, match } = this.props;
    const postParams = { id };
    if (isCurrentlyOn) {
      postParams.disassociate = true;
    }
    try {
      await postSuccess(match.params.id, postParams);
    } catch (err) {
      this.setState({ error: true });
    } finally {
      if (isCurrentlyOn) {
        // Remove it from state
        this.setState((prevState) => ({
          successTemplateIds: prevState.successTemplateIds.filter((templateId) => templateId !== id)
        }));
      } else {
        // Add it to state
        this.setState(prevState => ({
          successTemplateIds: [...prevState.successTemplateIds, id]
        }));
      }
    }
  }

  async fetchNotifications (queryParams) {
    const { noInitialResults } = this.state;
    const { getNotifications, getSuccess, getError, match } = this.props;
    const { page, page_size, order_by } = queryParams;

    let sortOrder = 'ascending';
    let sortedColumnKey = order_by;

    if (order_by.startsWith('-')) {
      sortOrder = 'descending';
      sortedColumnKey = order_by.substring(1);
    }

    this.setState({ error: false, loading: true });

    try {
      const { data } = await getNotifications(match.params.id, queryParams);
      const { count, results } = data;

      const pageCount = Math.ceil(count / page_size);

      const stateToUpdate = {
        count,
        page,
        pageCount,
        page_size,
        sortOrder,
        sortedColumnKey,
        results,
        noInitialResults,
        selected: []
      };

      // This is in place to track whether or not the initial request
      // return any results.  If it did not, we show the empty state.
      // This will become problematic once search is in play because
      // the first load may have query params (think bookmarked search)
      if (typeof noInitialResults === 'undefined') {
        stateToUpdate.noInitialResults = results.length === 0;
      }

      this.setState(stateToUpdate);
      // TODO: remove this hack once tab query param is gone
      this.updateUrl({ ...queryParams, tab: 'notifications' });

      const notificationTemplateIds = results
        .map(notificationTemplate => notificationTemplate.id)
        .join(',');

      let successTemplateIds = [];
      let errorTemplateIds = [];

      if (results.length > 0) {
        const successTemplatesPromise = getSuccess(match.params.id, {
          id__in: notificationTemplateIds
        });
        const errorTemplatesPromise = getError(match.params.id, {
          id__in: notificationTemplateIds
        });
        const successTemplatesResult = await successTemplatesPromise;
        const errorTemplatesResult = await errorTemplatesPromise;

        successTemplateIds = successTemplatesResult.data.results
          .map(successTemplate => successTemplate.id);
        errorTemplateIds = errorTemplatesResult.data.results
          .map(errorTemplate => errorTemplate.id);
      }
      this.setState({
        successTemplateIds,
        errorTemplateIds
      });
    } catch (err) {
      this.setState({ error: true });
    } finally {
      this.setState({ loading: false });
    }
  }

  render () {
    const {
      count,
      error,
      loading,
      page,
      pageCount,
      page_size,
      sortedColumnKey,
      sortOrder,
      results,
      noInitialResults,
      selected,
      successTemplateIds,
      errorTemplateIds
    } = this.state;
    const { match } = this.props;
    const parentBreadcrumb = { name: i18nMark('Organizations'), url: match.url };

    return (
      <Fragment>
        {noInitialResults && (
          <EmptyState>
            <EmptyStateIcon icon={CubesIcon} />
            <Title size="lg">
              <Trans>No Notifictions Found</Trans>
            </Title>
            <EmptyStateBody>
              <Trans>Please add a notification template to populate this list</Trans>
            </EmptyStateBody>
          </EmptyState>
        )}
        {(
          typeof noInitialResults !== 'undefined'
          && !noInitialResults
          && !loading
          && !error
        ) && (
          <Fragment>
            <DataListToolbar
              isAllSelected={selected.length === results.length}
              sortedColumnKey={sortedColumnKey}
              sortOrder={sortOrder}
              columns={this.columns}
              onSearch={this.onSearch}
              onSort={this.onSort}
              onSelectAll={this.onSelectAll}
            />
            <I18n>
              {({ i18n }) => (
                <ul className="pf-c-data-list" aria-label={i18n._(t`Organizations List`)}>
                  {results.map(o => (
                    <NotificationListItem
                      key={o.id}
                      itemId={o.id}
                      name={o.name}
                      notificationType={o.notification_type}
                      detailUrl={`notifications/${o.id}`}
                      parentBreadcrumb={parentBreadcrumb}
                      isSelected={selected.includes(o.id)}
                      onSelect={() => this.onSelect(o.id)}
                      errorTurnedOn={errorTemplateIds.includes(o.id)}
                      toggleError={this.toggleError}
                      successTurnedOn={successTemplateIds.includes(o.id)}
                      toggleSuccess={this.toggleSuccess}
                    />
                  ))}
                </ul>
              )}
            </I18n>
            <Pagination
              count={count}
              page={page}
              pageCount={pageCount}
              page_size={page_size}
              pageSizeOptions={this.pageSizeOptions}
              onSetPage={this.onSetPage}
            />
          </Fragment>
        )}
        {loading ? <div>loading...</div> : ''}
        {error ? <div>error</div> : ''}
      </Fragment>
    );
  }
}

export default Notifications;
