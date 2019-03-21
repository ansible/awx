import React, {
  Component,
  Fragment
} from 'react';
import PropTypes from 'prop-types';
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

    this.handleSearch = this.handleSearch.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
    this.handleSort = this.handleSort.bind(this);
    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.toggleNotification = this.toggleNotification.bind(this);
    this.updateUrl = this.updateUrl.bind(this);
    this.createError = this.createError.bind(this);
    this.createSuccess = this.createSuccess.bind(this);
    this.readNotifications = this.readNotifications.bind(this);
  }

  componentDidMount () {
    const queryParams = this.getQueryParams();
    this.readNotifications(queryParams);
  }

  getQueryParams (overrides = {}) {
    const { location } = this.props;
    const { search } = location;

    const searchParams = parseQueryString(search.substring(1));

    return Object.assign({}, this.defaultParams, searchParams, overrides);
  }

  handleSort = (sortedColumnKey, sortOrder) => {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ order_by, page_size });

    this.readNotifications(queryParams);
  };

  handleSetPage = (pageNumber, pageSize) => {
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);

    const queryParams = this.getQueryParams({ page, page_size });

    this.readNotifications(queryParams);
  };

  handleSelectAll = isSelected => {
    const { results } = this.state;

    const selected = isSelected ? results.map(o => o.id) : [];

    this.setState({ selected });
  };

  toggleNotification = (id, isCurrentlyOn, status) => {
    if (status === 'success') {
      this.createSuccess(id, isCurrentlyOn);
    } else if (status === 'error') {
      this.createError(id, isCurrentlyOn);
    }
  };

  handleSearch () {
    const { sortedColumnKey, sortOrder } = this.state;

    this.handleSort(sortedColumnKey, sortOrder);
  }

  updateUrl (queryParams) {
    const { history, location, match } = this.props;
    const pathname = match.url;
    const search = `?${encodeQueryString(queryParams)}`;

    if (search !== location.search) {
      history.replace({ pathname, search });
    }
  }

  async createError (id, isCurrentlyOn) {
    const { onCreateError, match } = this.props;
    const postParams = { id };
    if (isCurrentlyOn) {
      postParams.disassociate = true;
    }
    try {
      await onCreateError(match.params.id, postParams);
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

  async createSuccess (id, isCurrentlyOn) {
    const { onCreateSuccess, match } = this.props;
    const postParams = { id };
    if (isCurrentlyOn) {
      postParams.disassociate = true;
    }
    try {
      await onCreateSuccess(match.params.id, postParams);
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

  async readNotifications (queryParams) {
    const { noInitialResults } = this.state;
    const { onReadNotifications, onReadSuccess, onReadError, match } = this.props;
    const { page, page_size, order_by } = queryParams;

    let sortOrder = 'ascending';
    let sortedColumnKey = order_by;

    if (order_by.startsWith('-')) {
      sortOrder = 'descending';
      sortedColumnKey = order_by.substring(1);
    }

    this.setState({ error: false, loading: true });

    try {
      const { data } = await onReadNotifications(match.params.id, queryParams);
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

      const notificationTemplateIds = results
        .map(notificationTemplate => notificationTemplate.id)
        .join(',');

      let successTemplateIds = [];
      let errorTemplateIds = [];

      if (results.length > 0) {
        const successTemplatesPromise = onReadSuccess(match.params.id, {
          id__in: notificationTemplateIds
        });
        const errorTemplatesPromise = onReadError(match.params.id, {
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
    return (
      <Fragment>
        {noInitialResults && (
          <EmptyState>
            <EmptyStateIcon icon={CubesIcon} />
            <Title size="lg">
              <Trans>No Notifications Found</Trans>
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
              onSearch={this.handleSearch}
              onSort={this.handleSort}
              onSelectAll={this.handleSelectAll}
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
                      detailUrl={`/notifications/${o.id}`}
                      toggleNotification={this.toggleNotification}
                      errorTurnedOn={errorTemplateIds.includes(o.id)}
                      successTurnedOn={successTemplateIds.includes(o.id)}
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
              onSetPage={this.handleSetPage}
            />
          </Fragment>
        )}
        {loading ? <div>loading...</div> : ''}
        {error ? <div>error</div> : ''}
      </Fragment>
    );
  }
}

Notifications.propTypes = {
  onReadError: PropTypes.func.isRequired,
  onReadNotifications: PropTypes.func.isRequired,
  onReadSuccess: PropTypes.func.isRequired,
  onCreateError: PropTypes.func.isRequired,
  onCreateSuccess: PropTypes.func.isRequired,
};

export default Notifications;
