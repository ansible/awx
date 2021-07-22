import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';
import { Toolbar, ToolbarContent } from '@patternfly/react-core';

import {
  parseQueryString,
  mergeParams,
  removeParams,
  updateQueryString,
} from 'util/qs';
import { QSConfig, SearchColumns, SortColumns } from 'types';
import DataListToolbar from '../DataListToolbar';

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
    this.handleReplaceSearch = this.handleReplaceSearch.bind(this);
    this.handleSort = this.handleSort.bind(this);
    this.handleRemove = this.handleRemove.bind(this);
    this.handleRemoveAll = this.handleRemoveAll.bind(this);
  }

  handleSearch(key, value) {
    const { location, qsConfig } = this.props;
    const params = parseQueryString(qsConfig, location.search);
    const qs = updateQueryString(qsConfig, location.search, {
      ...mergeParams(params, { [key]: value }),
      page: 1,
    });
    this.pushHistoryState(qs);
  }

  handleReplaceSearch(key, value) {
    const { location, qsConfig } = this.props;
    const qs = updateQueryString(qsConfig, location.search, {
      [key]: value,
    });
    this.pushHistoryState(qs);
  }

  handleRemove(key, value) {
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    const updatedParams = removeParams(qsConfig, oldParams, {
      [key]: value,
    });
    const qs = updateQueryString(qsConfig, location.search, updatedParams);
    this.pushHistoryState(qs);
  }

  handleRemoveAll() {
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    Object.keys(oldParams).forEach((key) => {
      oldParams[key] = null;
    });
    delete oldParams.page_size;
    delete oldParams.order_by;
    const qs = updateQueryString(qsConfig, location.search, oldParams);
    this.pushHistoryState(qs);
  }

  handleSort(key, order) {
    const { location, qsConfig } = this.props;
    const qs = updateQueryString(qsConfig, location.search, {
      order_by: order === 'ascending' ? key : `-${key}`,
      page: null,
    });
    this.pushHistoryState(qs);
  }

  pushHistoryState(queryString) {
    const { history } = this.props;
    const { pathname } = history.location;
    history.push(queryString ? `${pathname}?${queryString}` : pathname);
  }

  render() {
    const {
      emptyStateControls,
      itemCount,
      searchColumns,
      searchableKeys,
      relatedSearchableKeys,
      sortColumns,
      renderToolbar,
      qsConfig,
      location,
      pagination,
    } = this.props;
    const params = parseQueryString(qsConfig, location.search);
    const isEmpty = itemCount === 0 && Object.keys(params).length === 0;
    return (
      <>
        {isEmpty ? (
          <Toolbar
            id={`${qsConfig.namespace}-list-toolbar`}
            clearAllFilters={this.handleRemoveAll}
            collapseListedFiltersBreakpoint="lg"
          >
            <ToolbarContent>
              <EmptyStateControlsWrapper>
                {emptyStateControls}
              </EmptyStateControlsWrapper>
            </ToolbarContent>
          </Toolbar>
        ) : (
          <>
            {renderToolbar({
              itemCount,
              searchColumns,
              sortColumns,
              searchableKeys,
              relatedSearchableKeys,
              onSearch: this.handleSearch,
              onReplaceSearch: this.handleReplaceSearch,
              onSort: this.handleSort,
              onRemove: this.handleRemove,
              clearAllFilters: this.handleRemoveAll,
              qsConfig,
              pagination,
            })}
          </>
        )}
      </>
    );
  }
}

ListHeader.propTypes = {
  itemCount: PropTypes.number.isRequired,
  qsConfig: QSConfig.isRequired,
  searchColumns: SearchColumns.isRequired,
  searchableKeys: PropTypes.arrayOf(PropTypes.string),
  relatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  sortColumns: SortColumns,
  renderToolbar: PropTypes.func,
};

ListHeader.defaultProps = {
  renderToolbar: (props) => <DataListToolbar {...props} />,
  searchableKeys: [],
  sortColumns: null,
  relatedSearchableKeys: [],
};

export default withRouter(ListHeader);
