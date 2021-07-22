import React, { useEffect, useState } from 'react';
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
  Dropdown,
  DropdownPosition,
  KebabToggle,
} from '@patternfly/react-core';
import {
  AngleDownIcon,
  AngleRightIcon,
  SearchIcon,
} from '@patternfly/react-icons';
import { SearchColumns, SortColumns, QSConfig } from 'types';
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
  return (
    <Toolbar
      id={`${qsConfig.namespace}-list-toolbar`}
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
              <Checkbox
                isChecked={isAllSelected}
                onChange={onSelectAll}
                aria-label={t`Select all`}
                id="select-all"
              />
            </ToolbarItem>
          </ToolbarGroup>
        )}
        <ToolbarToggleGroup toggleIcon={<SearchIcon />} breakpoint="lg">
          <ToolbarItem>
            <Search
              qsConfig={qsConfig}
              columns={[
                ...searchColumns,
                { name: t`Advanced`, key: 'advanced' },
              ]}
              searchableKeys={searchableKeys}
              relatedSearchableKeys={relatedSearchableKeys}
              onSearch={onSearch}
              onReplaceSearch={onReplaceSearch}
              onShowAdvancedSearch={onShowAdvancedSearch}
              onRemove={onRemove}
              enableNegativeFiltering={enableNegativeFiltering}
              enableRelatedFuzzyFiltering={enableRelatedFuzzyFiltering}
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
            <>
              <ToolbarItem>
                <ExpandCollapse
                  isCompact={isCompact}
                  onCompact={onCompact}
                  onExpand={onExpand}
                />
              </ToolbarItem>
            </>
          </ToolbarGroup>
        )}
        {isAdvancedSearchShown && additionalControls.length > 0 && (
          <ToolbarItem>
            <KebabifiedProvider
              value={{
                isKebabified: true,
                onKebabModalChange: setIsKebabModalOpen,
              }}
            >
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
  searchableKeys: PropTypes.arrayOf(PropTypes.string),
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
};

export default DataListToolbar;
