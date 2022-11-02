/* eslint-disable react/jsx-no-useless-fragment */
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { Toolbar, ToolbarContent } from '@patternfly/react-core';

import {
  parseQueryString,
  mergeParams,
  removeParams,
  updateQueryString,
} from 'util/qs';
import { QSConfig, SearchColumns, SortColumns, SearchableKeys } from 'types';
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
function ListHeader(props) {
  const { search, pathname } = useLocation();
  const [isFilterCleared, setIsFilterCleared] = useState(false);
  const history = useHistory();
  const {
    emptyStateControls,
    itemCount,
    pagination,
    qsConfig,
    relatedSearchableKeys,
    renderToolbar,
    searchColumns,
    searchableKeys,
    sortColumns,
  } = props;

  const handleSearch = (key, value) => {
    const params = parseQueryString(qsConfig, search);
    const qs = updateQueryString(qsConfig, search, {
      ...mergeParams(params, { [key]: value }),
      page: 1,
    });
    pushHistoryState(qs);
  };

  const handleReplaceSearch = (key, value) => {
    const qs = updateQueryString(qsConfig, search, {
      [key]: value,
    });
    pushHistoryState(qs);
  };

  const handleRemove = (key, value) => {
    const oldParams = parseQueryString(qsConfig, search);
    const updatedParams = removeParams(qsConfig, oldParams, {
      [key]: value,
    });
    const qs = updateQueryString(qsConfig, search, updatedParams);
    pushHistoryState(qs);
  };

  const handleRemoveAll = () => {
    const oldParams = parseQueryString(qsConfig, search);
    Object.keys(oldParams).forEach((key) => {
      oldParams[key] = null;
    });
    delete oldParams.page_size;
    delete oldParams.order_by;
    const qs = updateQueryString(qsConfig, search, oldParams);
    setIsFilterCleared(true);
    pushHistoryState(qs);
  };

  const handleSort = (key, order) => {
    const qs = updateQueryString(qsConfig, search, {
      order_by: order === 'ascending' ? key : `-${key}`,
      page: null,
    });
    pushHistoryState(qs);
  };

  const pushHistoryState = (queryString) => {
    history.push(queryString ? `${pathname}?${queryString}` : pathname);
  };

  const params = parseQueryString(qsConfig, search);
  const isEmpty = itemCount === 0 && Object.keys(params).length === 0;
  return (
    <>
      {isEmpty ? (
        <Toolbar
          id={`${qsConfig.namespace}-list-toolbar`}
          clearAllFilters={handleRemoveAll}
          collapseListedFiltersBreakpoint="lg"
          ouiaId={`${qsConfig.namespace}-list-toolbar`}
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
            onSearch: handleSearch,
            onReplaceSearch: handleReplaceSearch,
            onSort: handleSort,
            onRemove: handleRemove,
            clearAllFilters: handleRemoveAll,
            qsConfig,
            pagination,
            isFilterCleared,
          })}
        </>
      )}
    </>
  );
}

ListHeader.propTypes = {
  itemCount: PropTypes.number.isRequired,
  qsConfig: QSConfig.isRequired,
  searchColumns: SearchColumns.isRequired,
  searchableKeys: SearchableKeys,
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

export default ListHeader;
