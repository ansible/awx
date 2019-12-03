import React, { Fragment } from 'react';
import PropTypes, { arrayOf, shape, string, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';

import DataListToolbar from '@components/DataListToolbar';
import FilterTags from '@components/FilterTags';

import {
  encodeNonDefaultQueryString,
  parseQueryString,
  mergeParams,
  replaceParams,
  removeParams,
} from '@util/qs';
import { QSConfig } from '@types';

const EmptyStateControlsWrapper = styled.div`
  display: flex;
  margin-top: 20px;
  margin-right: 20px;
  margin-bottom: 20px;
  justify-content: flex-end;

  & > :not(:first-child) {
    margin-left: 20px;
  }
`;
class ListHeader extends React.Component {
  constructor(props) {
    super(props);

    this.handleSearch = this.handleSearch.bind(this);
    this.handleSort = this.handleSort.bind(this);
    this.handleRemove = this.handleRemove.bind(this);
    this.handleRemoveAll = this.handleRemoveAll.bind(this);
  }

  getSortOrder() {
    const { qsConfig, location } = this.props;
    const queryParams = parseQueryString(qsConfig, location.search);
    if (queryParams.order_by && queryParams.order_by.startsWith('-')) {
      return [queryParams.order_by.substr(1), 'descending'];
    }
    return [queryParams.order_by, 'ascending'];
  }

  handleSearch(key, value) {
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    this.pushHistoryState(mergeParams(oldParams, { [key]: value }));
  }

  handleRemove(key, value) {
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    this.pushHistoryState(removeParams(qsConfig, oldParams, { [key]: value }));
  }

  handleRemoveAll() {
    this.pushHistoryState(null);
  }

  handleSort(key, order) {
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    this.pushHistoryState(
      replaceParams(oldParams, {
        order_by: order === 'ascending' ? key : `-${key}`,
        page: null,
      })
    );
  }

  pushHistoryState(params) {
    const { history, qsConfig } = this.props;
    const { pathname } = history.location;
    const encodedParams = encodeNonDefaultQueryString(qsConfig, params);
    history.push(encodedParams ? `${pathname}?${encodedParams}` : pathname);
  }

  render() {
    const {
      emptyStateControls,
      itemCount,
      columns,
      renderToolbar,
      qsConfig,
      location,
    } = this.props;
    const [orderBy, sortOrder] = this.getSortOrder();
    const params = parseQueryString(qsConfig, location.search);
    const isEmpty = itemCount === 0 && Object.keys(params).length === 0;
    return (
      <Fragment>
        {isEmpty ? (
          <Fragment>
            <EmptyStateControlsWrapper>
              {emptyStateControls}
            </EmptyStateControlsWrapper>
            <FilterTags
              itemCount={itemCount}
              qsConfig={qsConfig}
              onRemove={this.handleRemove}
              onRemoveAll={this.handleRemoveAll}
            />
          </Fragment>
        ) : (
          <Fragment>
            {renderToolbar({
              sortedColumnKey: orderBy,
              sortOrder,
              columns,
              onSearch: this.handleSearch,
              onSort: this.handleSort,
              qsConfig,
            })}
            <FilterTags
              itemCount={itemCount}
              qsConfig={qsConfig}
              onRemove={this.handleRemove}
              onRemoveAll={this.handleRemoveAll}
            />
          </Fragment>
        )}
      </Fragment>
    );
  }
}

ListHeader.propTypes = {
  itemCount: PropTypes.number.isRequired,
  qsConfig: QSConfig.isRequired,
  columns: arrayOf(
    shape({
      name: string.isRequired,
      key: string.isRequired,
      isSortable: bool,
      isSearchable: bool,
    })
  ).isRequired,
  renderToolbar: PropTypes.func,
};

ListHeader.defaultProps = {
  renderToolbar: props => <DataListToolbar {...props} />,
};

export default withRouter(ListHeader);
