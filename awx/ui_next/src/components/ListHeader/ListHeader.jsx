import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';
import { Toolbar, ToolbarContent } from '@patternfly/react-core';
import DataListToolbar from '../DataListToolbar';

import {
  encodeNonDefaultQueryString,
  parseQueryString,
  mergeParams,
  replaceParams,
  removeParams,
} from '../../util/qs';
import { QSConfig, SearchColumns, SortColumns } from '../../types';

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
    let params = parseQueryString(qsConfig, location.search);
    params = mergeParams(params, { [key]: value });
    params = replaceParams(params, { page: 1 });
    this.pushHistoryState(params);
  }

  handleReplaceSearch(key, value) {
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    this.pushHistoryState(replaceParams(oldParams, { [key]: value }));
  }

  handleRemove(key, value) {
    const { location, qsConfig } = this.props;
    let oldParams = parseQueryString(qsConfig, location.search);
    if (parseInt(value, 10)) {
      oldParams = removeParams(qsConfig, oldParams, {
        [key]: parseInt(value, 10),
      });
    }
    this.pushHistoryState(removeParams(qsConfig, oldParams, { [key]: value }));
  }

  handleRemoveAll() {
    // remove everything in oldParams except for page_size and order_by
    const { location, qsConfig } = this.props;
    const oldParams = parseQueryString(qsConfig, location.search);
    const oldParamsClone = { ...oldParams };
    delete oldParamsClone.page_size;
    delete oldParamsClone.order_by;
    this.pushHistoryState(removeParams(qsConfig, oldParams, oldParamsClone));
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
      <Fragment>
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
          <Fragment>
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
          </Fragment>
        )}
      </Fragment>
    );
  }
}

ListHeader.propTypes = {
  itemCount: PropTypes.number.isRequired,
  qsConfig: QSConfig.isRequired,
  searchColumns: SearchColumns.isRequired,
  searchableKeys: PropTypes.arrayOf(PropTypes.string),
  relatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  sortColumns: SortColumns.isRequired,
  renderToolbar: PropTypes.func,
};

ListHeader.defaultProps = {
  renderToolbar: props => <DataListToolbar {...props} />,
  searchableKeys: [],
  relatedSearchableKeys: [],
};

export default withRouter(ListHeader);
