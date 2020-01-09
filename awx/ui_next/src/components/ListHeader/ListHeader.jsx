import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';
import {
  DataToolbar,
  DataToolbarContent,
} from '@patternfly/react-core/dist/umd/experimental';
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
          <DataToolbar
            id={`${qsConfig.namespace}-list-toolbar`}
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
          <Fragment>
            {renderToolbar({
              searchColumns,
              sortColumns,
              onSearch: this.handleSearch,
              onReplaceSearch: this.handleReplaceSearch,
              onSort: this.handleSort,
              onRemove: this.handleRemove,
              clearAllFilters: this.handleRemoveAll,
              qsConfig,
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
  sortColumns: SortColumns.isRequired,
  renderToolbar: PropTypes.func,
};

ListHeader.defaultProps = {
  renderToolbar: props => <DataListToolbar {...props} />,
};

export default withRouter(ListHeader);
