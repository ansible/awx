import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Checkbox } from '@patternfly/react-core';
import styled from 'styled-components';
import { SearchIcon } from '@patternfly/react-icons';
import {
  DataToolbar,
  DataToolbarContent,
  DataToolbarGroup,
  DataToolbarToggleGroup,
  DataToolbarItem,
} from '@patternfly/react-core/dist/umd/experimental';
import ExpandCollapse from '../ExpandCollapse';
import Search from '../Search';
import Sort from '../Sort';

import { SearchColumns, SortColumns, QSConfig } from '@types';

const AdditionalControlsWrapper = styled.div`
  display: flex;
  flex-grow: 1;
  justify-content: flex-end;
  align-items: center;

  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

const AdditionalControlsDataToolbarGroup = styled(DataToolbarGroup)`
  margin-left: auto;
  margin-right: 0 !important;
`;

const DataToolbarSeparator = styled(DataToolbarItem)`
  width: 1px !important;
  height: 30px !important;
  margin-left: 3px !important;
  margin-right: 10px !important;
`;

class DataListToolbar extends React.Component {
  render() {
    const {
      clearAllFilters,
      searchColumns,
      sortColumns,
      showSelectAll,
      isAllSelected,
      isCompact,
      onSort,
      onSearch,
      onReplaceSearch,
      onRemove,
      onCompact,
      onExpand,
      onSelectAll,
      additionalControls,
      i18n,
      qsConfig,
    } = this.props;

    const showExpandCollapse = onCompact && onExpand;
    return (
      <DataToolbar
        id={`${qsConfig.namespace}-list-toolbar`}
        clearAllFilters={clearAllFilters}
        collapseListedFiltersBreakpoint="lg"
      >
        <DataToolbarContent>
          {showSelectAll && (
            <DataToolbarGroup>
              <DataToolbarItem>
                <Checkbox
                  isChecked={isAllSelected}
                  onChange={onSelectAll}
                  aria-label={i18n._(t`Select all`)}
                  id="select-all"
                />
              </DataToolbarItem>
              <DataToolbarSeparator variant="separator" />
            </DataToolbarGroup>
          )}
          <DataToolbarToggleGroup toggleIcon={<SearchIcon />} breakpoint="lg">
            <DataToolbarItem>
              <Search
                qsConfig={qsConfig}
                columns={searchColumns}
                onSearch={onSearch}
                onReplaceSearch={onReplaceSearch}
                onRemove={onRemove}
              />
            </DataToolbarItem>
            <DataToolbarItem>
              <Sort qsConfig={qsConfig} columns={sortColumns} onSort={onSort} />
            </DataToolbarItem>
          </DataToolbarToggleGroup>
          <DataToolbarGroup>
            {showExpandCollapse && (
              <Fragment>
                <DataToolbarItem>
                  <ExpandCollapse
                    isCompact={isCompact}
                    onCompact={onCompact}
                    onExpand={onExpand}
                  />
                </DataToolbarItem>
              </Fragment>
            )}
          </DataToolbarGroup>
          <AdditionalControlsDataToolbarGroup>
            <DataToolbarItem>
              <AdditionalControlsWrapper>
                {additionalControls}
              </AdditionalControlsWrapper>
            </DataToolbarItem>
          </AdditionalControlsDataToolbarGroup>
        </DataToolbarContent>
      </DataToolbar>
    );
  }
}

DataListToolbar.propTypes = {
  clearAllFilters: PropTypes.func,
  qsConfig: QSConfig.isRequired,
  searchColumns: SearchColumns.isRequired,
  sortColumns: SortColumns.isRequired,
  showSelectAll: PropTypes.bool,
  isAllSelected: PropTypes.bool,
  isCompact: PropTypes.bool,
  onCompact: PropTypes.func,
  onExpand: PropTypes.func,
  onSearch: PropTypes.func,
  onReplaceSearch: PropTypes.func,
  onSelectAll: PropTypes.func,
  onSort: PropTypes.func,
  additionalControls: PropTypes.arrayOf(PropTypes.node),
};

DataListToolbar.defaultProps = {
  clearAllFilters: null,
  showSelectAll: false,
  isAllSelected: false,
  isCompact: false,
  onCompact: null,
  onExpand: null,
  onSearch: null,
  onReplaceSearch: null,
  onSelectAll: null,
  onSort: null,
  additionalControls: [],
};

export default withI18n()(DataListToolbar);
