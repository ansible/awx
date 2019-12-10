import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';
import { DataToolbar, DataToolbarContent } from '@patternfly/react-core/dist/esm/experimental';
import DataListToolbar from '@components/DataListToolbar';

import {
  encodeNonDefaultQueryString,
  parseQueryString,
  mergeParams,
  replaceParams,
  removeParams,
} from '@util/qs';
import { QSConfig, SearchColumns, SortColumns } from '@types';

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
      searchColumns,
      sortColumns,
      renderToolbar,
      qsConfig,
      location,
    } = this.props;
    const params = parseQueryString(qsConfig, location.search);
    const isEmpty = itemCount === 0 && Object.keys(params).length === 0;
    return (
      <Fragment>
        {isEmpty ? (
          <DataToolbar id={`${qsConfig.namespace}-list-toolbar`}
            clearAllFilters={this.handleRemoveAll}
            collapseListedFiltersBreakpoint="md"
          >
            <DataToolbarContent>
              <EmptyStateControlsWrapper>
                {emptyStateControls}
              </EmptyStateControlsWrapper>
            </DataToolbarContent>
          </DataToolbar>
        ) : (
          <DataToolbar id={`${qsConfig.namespace}-list-toolbar`}
            clearAllFilters={this.handleRemoveAll}
            collapseListedFiltersBreakpoint="xl"
          >
            <DataToolbarContent>
              {renderToolbar({
                searchColumns,
                sortColumns,
                onSearch: this.handleSearch,
                onSort: this.handleSort,
                onRemove: this.handleRemove,
                qsConfig,
              })}
            </DataToolbarContent>
          </DataToolbar>
        )}
      </Fragment>
    );
  }
}

ListHeader.propTypes = {
  itemCount: PropTypes.number.isRequired,
  qsConfig: QSConfig.isRequired,
  searchColumns: SearchColumns.isRequired,
  sortColumns: SortColumns.isRequired,
  renderToolbar: PropTypes.func,
};

ListHeader.defaultProps = {
  renderToolbar: props => <DataListToolbar {...props} />,
};

export default withRouter(ListHeader);
