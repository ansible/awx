import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Checkbox,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
  ToolbarToggleGroup,
  Dropdown,
  KebabToggle,
} from '@patternfly/react-core';
import { SearchIcon } from '@patternfly/react-icons';
import ExpandCollapse from '../ExpandCollapse';
import Search from '../Search';
import Sort from '../Sort';
import { SearchColumns, SortColumns, QSConfig } from '../../types';
import { KebabifiedProvider } from '../../contexts/Kebabified';

function DataListToolbar({
  itemCount,
  clearAllFilters,
  searchColumns,
  searchableKeys,
  relatedSearchableKeys,
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
  pagination,
}) {
  const showExpandCollapse = onCompact && onExpand;
  const [isKebabOpen, setIsKebabOpen] = useState(false);
  const [isKebabModalOpen, setIsKebabModalOpen] = useState(false);
  const [isAdvancedSearchShown, setIsAdvancedSearchShown] = useState(false);

  const onShowAdvancedSearch = shown => {
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
      clearFiltersButtonText={i18n._(t`Clear all filters`)}
    >
      <ToolbarContent>
        {showSelectAll && (
          <ToolbarGroup>
            <ToolbarItem>
              <Checkbox
                isChecked={isAllSelected}
                onChange={onSelectAll}
                aria-label={i18n._(t`Select all`)}
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
                { name: i18n._(t`Advanced`), key: 'advanced' },
              ]}
              searchableKeys={searchableKeys}
              relatedSearchableKeys={relatedSearchableKeys}
              onSearch={onSearch}
              onReplaceSearch={onReplaceSearch}
              onShowAdvancedSearch={onShowAdvancedSearch}
              onRemove={onRemove}
            />
          </ToolbarItem>
          <ToolbarItem>
            <Sort qsConfig={qsConfig} columns={sortColumns} onSort={onSort} />
          </ToolbarItem>
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
                    onToggle={isOpen => {
                      if (!isKebabModalOpen) {
                        setIsKebabOpen(isOpen);
                      }
                    }}
                  />
                }
                isOpen={isKebabOpen}
                isPlain
                dropdownItems={additionalControls}
              />
            </KebabifiedProvider>
          </ToolbarItem>
        )}
        {!isAdvancedSearchShown && (
          <ToolbarGroup>
            {additionalControls.map(control => (
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
  itemCount: 0,
  searchableKeys: [],
  relatedSearchableKeys: [],
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
