import React, { useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import {
  Button,
  Checkbox,
  Toolbar,
  ToolbarContent as PFToolbarContent,
  ToolbarGroup,
  ToolbarItem,
  ToolbarToggleGroup,
  Tooltip,
  Dropdown,
  DropdownPosition,
  KebabToggle,
} from '@patternfly/react-core';
import {
  AngleDownIcon,
  AngleRightIcon,
  SearchIcon,
} from '@patternfly/react-icons';
import { SearchColumns, SortColumns, QSConfig, SearchableKeys } from 'types';
import { KebabifiedProvider } from 'contexts/Kebabified';
import ExpandCollapse from '../ExpandCollapse';
import Search from '../Search';
import Sort from '../Sort';

const ToolbarContent = styled(PFToolbarContent)`
  & > .pf-c-toolbar__content-section {
    flex-wrap: nowrap;
  }
`;

function DataListToolbar({
  isAllExpanded,
  onExpandAll,
  itemCount,
  clearAllFilters,
  searchColumns,
  searchableKeys,
  relatedSearchableKeys,
  sortColumns,
  isAllSelected,
  onSelectAll,
  isCompact,
  onSort,
  onSearch,
  onReplaceSearch,
  onRemove,
  onCompact,
  onExpand,
  additionalControls,
  qsConfig,
  pagination,
  enableNegativeFiltering,
  enableRelatedFuzzyFiltering,
  handleIsAnsibleFactsSelected,
  isFilterCleared,
  advancedSearchDisabled,
}) {
  const showExpandCollapse = onCompact && onExpand;
  const [isKebabOpen, setIsKebabOpen] = useState(false);
  const [isKebabModalOpen, setIsKebabModalOpen] = useState(false);
  const [isAdvancedSearchShown, setIsAdvancedSearchShown] = useState(false);

  const viewportWidth =
    window.innerWidth || document.documentElement.clientWidth;
  const dropdownPosition =
    viewportWidth >= 992 ? DropdownPosition.right : DropdownPosition.left;

  const onShowAdvancedSearch = (shown) => {
    setIsAdvancedSearchShown(shown);
    setIsKebabOpen(false);
  };

  useEffect(() => {
    if (!isKebabModalOpen) {
      setIsKebabOpen(false);
    }
  }, [isKebabModalOpen]);

  const kebabProviderValue = useMemo(
    () => ({
      isKebabified: true,
      onKebabModalChange: setIsKebabModalOpen,
    }),
    [setIsKebabModalOpen]
  );
  const columns = [...searchColumns];
  if ( !advancedSearchDisabled ) {
      columns.push({ name: t`Advanced`, key: 'advanced' });
  }
  return (
    <Toolbar
      id={`${qsConfig.namespace}-list-toolbar`}
      ouiaId={`${qsConfig.namespace}-list-toolbar`}
      clearAllFilters={clearAllFilters}
      collapseListedFiltersBreakpoint="lg"
      clearFiltersButtonText={t`Clear all filters`}
    >
      <ToolbarContent>
        {onExpandAll && (
          <ToolbarGroup>
            <ToolbarItem>
              <Button
                onClick={() => {
                  onExpandAll(!isAllExpanded);
                }}
                aria-label={t`Expand all rows`}
                ouiaId="expand-all-rows"
                variant="plain"
              >
                {isAllExpanded ? (
                  <AngleDownIcon aria-label={t`Is expanded`} />
                ) : (
                  <AngleRightIcon aria-label={t`Is not expanded`} />
                )}
              </Button>
            </ToolbarItem>
          </ToolbarGroup>
        )}
        {onSelectAll && (
          <ToolbarGroup>
            <ToolbarItem>
              <Tooltip content={t`Select all`} position="top">
                <Checkbox
                  isChecked={isAllSelected}
                  onChange={onSelectAll}
                  aria-label={t`Select all`}
                  id="select-all"
                  ouiaId="select-all"
                />
              </Tooltip>
            </ToolbarItem>
          </ToolbarGroup>
        )}
        <ToolbarToggleGroup toggleIcon={<SearchIcon />} breakpoint="lg">
          <ToolbarItem>
            <Search
              qsConfig={qsConfig}
              columns={columns}
              searchableKeys={searchableKeys}
              relatedSearchableKeys={relatedSearchableKeys}
              onSearch={onSearch}
              onReplaceSearch={onReplaceSearch}
              onShowAdvancedSearch={onShowAdvancedSearch}
              onRemove={onRemove}
              enableNegativeFiltering={enableNegativeFiltering}
              enableRelatedFuzzyFiltering={enableRelatedFuzzyFiltering}
              handleIsAnsibleFactsSelected={handleIsAnsibleFactsSelected}
              isFilterCleared={isFilterCleared}
            />
          </ToolbarItem>
          {sortColumns && (
            <ToolbarItem>
              <Sort qsConfig={qsConfig} columns={sortColumns} onSort={onSort} />
            </ToolbarItem>
          )}
        </ToolbarToggleGroup>
        {showExpandCollapse && (
          <ToolbarGroup>
            <ToolbarItem>
              <ExpandCollapse
                isCompact={isCompact}
                onCompact={onCompact}
                onExpand={onExpand}
              />
            </ToolbarItem>
          </ToolbarGroup>
        )}
        {isAdvancedSearchShown && additionalControls.length > 0 && (
          <ToolbarItem>
            <KebabifiedProvider value={kebabProviderValue}>
              <Dropdown
                toggle={
                  <KebabToggle
                    data-cy="actions-kebab-toogle"
                    onToggle={(isOpen) => {
                      if (!isKebabModalOpen) {
                        setIsKebabOpen(isOpen);
                      }
                    }}
                  />
                }
                isOpen={isKebabOpen}
                position={dropdownPosition}
                isPlain
                dropdownItems={additionalControls}
                ouiaId="actions-dropdown"
              />
            </KebabifiedProvider>
          </ToolbarItem>
        )}
        {!isAdvancedSearchShown && (
          <ToolbarGroup>
            {additionalControls.map((control) => (
              <ToolbarItem key={control.key}>{control}</ToolbarItem>
            ))}
          </ToolbarGroup>
        )}
        {!isAdvancedSearchShown && pagination && itemCount > 0 && (
          <ToolbarItem variant="pagination">{pagination}</ToolbarItem>
        )}
      </ToolbarContent>
    </Toolbar>
  );
}

DataListToolbar.propTypes = {
  itemCount: PropTypes.number,
  clearAllFilters: PropTypes.func,
  qsConfig: QSConfig.isRequired,
  searchColumns: SearchColumns.isRequired,
  searchableKeys: SearchableKeys,
  relatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  sortColumns: SortColumns,
  isAllSelected: PropTypes.bool,
  isCompact: PropTypes.bool,
  onCompact: PropTypes.func,
  onExpand: PropTypes.func,
  onSearch: PropTypes.func,
  onReplaceSearch: PropTypes.func,
  onSelectAll: PropTypes.func,
  onSort: PropTypes.func,
  additionalControls: PropTypes.arrayOf(PropTypes.node),
  enableNegativeFiltering: PropTypes.bool,
  enableRelatedFuzzyFiltering: PropTypes.bool,
  advancedSearchDisabled : PropTypes.bool,
};

DataListToolbar.defaultProps = {
  itemCount: 0,
  searchableKeys: [],
  relatedSearchableKeys: [],
  sortColumns: null,
  clearAllFilters: null,
  isAllSelected: false,
  isCompact: false,
  onCompact: null,
  onExpand: null,
  onSearch: null,
  onReplaceSearch: null,
  onSelectAll: null,
  onSort: null,
  additionalControls: [],
  enableNegativeFiltering: true,
  enableRelatedFuzzyFiltering: true,
  advancedSearchDisabled: false,
};

export default DataListToolbar;
