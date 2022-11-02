import 'styled-components/macro';
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { useLocation } from 'react-router-dom';
import {
  Button,
  ButtonVariant,
  InputGroup,
  Select,
  SelectOption,
  SelectVariant,
  TextInput,
  ToolbarGroup,
  ToolbarItem,
  ToolbarFilter,
} from '@patternfly/react-core';
import { SearchIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { parseQueryString } from 'util/qs';
import { QSConfig, SearchColumns, SearchableKeys } from 'types';
import AdvancedSearch from './AdvancedSearch';
import getChipsByKey from './getChipsByKey';

const NoOptionDropdown = styled.div`
  align-self: stretch;
  border: 1px solid var(--pf-global--BorderColor--300);
  padding: 5px 15px;
  white-space: nowrap;
  border-bottom-color: var(--pf-global--BorderColor--200);
`;

function Search({
  columns,
  onSearch,
  onReplaceSearch,
  onRemove,
  qsConfig,
  searchableKeys,
  relatedSearchableKeys,
  onShowAdvancedSearch,
  isDisabled,
  maxSelectHeight,
  enableNegativeFiltering,
  enableRelatedFuzzyFiltering,
  handleIsAnsibleFactsSelected,
  isFilterCleared,
}) {
  const location = useLocation();
  const [isSearchDropdownOpen, setIsSearchDropdownOpen] = useState(false);
  const [searchKey, setSearchKey] = useState(
    (() => {
      const defaultColumn = columns.filter((col) => col.isDefault);

      if (defaultColumn.length !== 1) {
        throw new Error(
          'One (and only one) searchColumn must be marked isDefault: true'
        );
      }

      return defaultColumn[0]?.key;
    })()
  );
  const [searchValue, setSearchValue] = useState('');
  const [isFilterDropdownOpen, setIsFilterDropdownOpen] = useState(false);

  const params = parseQueryString(qsConfig, location.search);
  if (params?.host_filter) {
    params.ansible_facts = params.host_filter.substring(
      'ansible_facts__'.length
    );
    delete params.host_filter;
  }

  const searchChips = getChipsByKey(params, columns, qsConfig);
  const [chipsByKey, setChipsByKey] = useState(
    JSON.parse(JSON.stringify(searchChips))
  );

  useEffect(() => {
    Object.keys(chipsByKey).forEach((el) => {
      chipsByKey[el].chips = [];
    });
    setChipsByKey({ ...chipsByKey, ...searchChips });
  }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDropdownSelect = ({ target }) => {
    const { key: actualSearchKey } = columns.find(
      ({ name }) => name === target.innerText
    );
    onShowAdvancedSearch(actualSearchKey === 'advanced');
    setIsFilterDropdownOpen(false);
    setSearchKey(actualSearchKey);
  };

  const handleSearch = (e) => {
    // keeps page from fully reloading
    e.preventDefault();

    if (searchValue) {
      onSearch(searchKey, searchValue);
      setSearchValue('');
    }
  };

  const handleTextKeyDown = (e) => {
    if (e.key && e.key === 'Enter') {
      handleSearch(e);
    }
  };

  const handleFilterDropdownSelect = (key, event, actualValue) => {
    if (event.target.checked) {
      onSearch(key, actualValue);
    } else {
      onRemove(key, actualValue);
    }
  };

  const { name: searchColumnName } = columns.find(
    ({ key }) => key === searchKey
  );

  const searchOptions = columns
    .filter(({ key }) => key !== searchKey)
    .map(({ key, name }) => (
      <SelectOption
        data-cy={`select-option-${key}`}
        id={`select-option-${key}`}
        key={key}
        value={name}
      >
        {name}
      </SelectOption>
    ));

  return (
    <ToolbarGroup variant="filter-group">
      <ToolbarItem>
        {searchOptions.length > 0 ? (
          <Select
            variant={SelectVariant.single}
            className="simpleKeySelect"
            aria-label={t`Simple key select`}
            typeAheadAriaLabel={t`Simple key select`}
            onToggle={setIsSearchDropdownOpen}
            onSelect={handleDropdownSelect}
            selections={searchColumnName}
            isOpen={isSearchDropdownOpen}
            ouiaId="simple-key-select"
            isDisabled={isDisabled}
            noResultsFoundText={t`No results found`}
          >
            {searchOptions}
          </Select>
        ) : (
          <NoOptionDropdown>{searchColumnName}</NoOptionDropdown>
        )}
      </ToolbarItem>
      {columns.map(({ key, name, options, isBoolean, booleanLabels = {} }) => (
        <ToolbarFilter
          chips={chipsByKey[key] ? chipsByKey[key].chips : []}
          deleteChip={(unusedKey, chip) => {
            const [columnKey, ...value] = chip.key.split(':');
            onRemove(columnKey, value.join(':'));
          }}
          categoryName={chipsByKey[key] ? chipsByKey[key].label : key}
          key={key}
          showToolbarItem={searchKey === key}
        >
          {(key === 'advanced' && (
            <AdvancedSearch
              onSearch={onSearch}
              searchableKeys={searchableKeys}
              relatedSearchableKeys={relatedSearchableKeys}
              maxSelectHeight={maxSelectHeight}
              enableNegativeFiltering={enableNegativeFiltering}
              enableRelatedFuzzyFiltering={enableRelatedFuzzyFiltering}
              handleIsAnsibleFactsSelected={handleIsAnsibleFactsSelected}
              isFilterCleared={isFilterCleared}
            />
          )) ||
            (options && (
              <Select
                variant={SelectVariant.checkbox}
                aria-label={name}
                typeAheadAriaLabel={name}
                onToggle={setIsFilterDropdownOpen}
                onSelect={(event, selection) =>
                  handleFilterDropdownSelect(key, event, selection)
                }
                selections={chipsByKey[key]?.chips.map((chip) => {
                  const [, ...value] = chip.key.split(':');
                  return value.join(':');
                })}
                isOpen={isFilterDropdownOpen}
                placeholderText={t`Filter By ${name}`}
                ouiaId={`filter-by-${key}`}
                isDisabled={isDisabled}
                maxHeight={maxSelectHeight}
                noResultsFoundText={t`No results found`}
              >
                {options.map(([optionKey, optionLabel]) => (
                  <SelectOption
                    key={optionKey}
                    value={optionKey}
                    inputId={`select-option-${optionKey}`}
                  >
                    {optionLabel}
                  </SelectOption>
                ))}
              </Select>
            )) ||
            (isBoolean && (
              <Select
                aria-label={name}
                onToggle={setIsFilterDropdownOpen}
                onSelect={(event, selection) => onReplaceSearch(key, selection)}
                selections={chipsByKey[key].chips[0]?.label}
                isOpen={isFilterDropdownOpen}
                placeholderText={t`Filter By ${name}`}
                ouiaId={`filter-by-${key}`}
                isDisabled={isDisabled}
                maxHeight={maxSelectHeight}
                noResultsFoundText={t`No results found`}
              >
                <SelectOption key="true" value="true">
                  {booleanLabels.true || t`Yes`}
                </SelectOption>
                <SelectOption key="false" value="false">
                  {booleanLabels.false || t`No`}
                </SelectOption>
              </Select>
            )) || (
              <InputGroup>
                {/* TODO: add support for dates:
          qsConfig.dateFields.filter(field => field === key).length && "date" */}
                <TextInput
                  data-cy="search-text-input"
                  type={
                    (qsConfig.integerFields.find(
                      (field) => field === searchKey
                    ) &&
                      'number') ||
                    'search'
                  }
                  aria-label={t`Search text input`}
                  value={searchValue}
                  onChange={setSearchValue}
                  onKeyDown={handleTextKeyDown}
                  isDisabled={isDisabled}
                />
                <div css={!searchValue && `cursor:not-allowed`}>
                  <Button
                    ouiaId="search-submit-button"
                    variant={ButtonVariant.control}
                    isDisabled={!searchValue || isDisabled}
                    aria-label={t`Search submit button`}
                    onClick={handleSearch}
                  >
                    <SearchIcon />
                  </Button>
                </div>
              </InputGroup>
            )}
        </ToolbarFilter>
      ))}
      {/* Add a ToolbarFilter for any key that doesn't have it's own
      search column so the chips show up */}
      {Object.keys(chipsByKey)
        .filter((val) => columns.map((val2) => val2.key).indexOf(val) === -1)
        .map((leftoverKey) => (
          <ToolbarFilter
            chips={chipsByKey[leftoverKey] ? chipsByKey[leftoverKey].chips : []}
            deleteChip={(unusedKey, chip) => {
              const [columnKey, ...value] = chip.key.split(':');
              if (columnKey === 'ansible_facts') {
                onRemove('host_filter', `${columnKey}__${value}`);
              } else {
                onRemove(columnKey, value.join(':'));
              }
            }}
            categoryName={
              chipsByKey[leftoverKey]
                ? chipsByKey[leftoverKey].label
                : leftoverKey
            }
            key={leftoverKey}
          />
        ))}
    </ToolbarGroup>
  );
}

Search.propTypes = {
  qsConfig: QSConfig.isRequired,
  columns: SearchColumns.isRequired,
  onSearch: PropTypes.func,
  onRemove: PropTypes.func,
  onShowAdvancedSearch: PropTypes.func.isRequired,
  isDisabled: PropTypes.bool,
  maxSelectHeight: PropTypes.string,
  enableNegativeFiltering: PropTypes.bool,
  enableRelatedFuzzyFiltering: PropTypes.bool,
  searchableKeys: SearchableKeys,
};

Search.defaultProps = {
  onSearch: null,
  onRemove: null,
  isDisabled: false,
  maxSelectHeight: '300px',
  enableNegativeFiltering: true,
  enableRelatedFuzzyFiltering: true,
  searchableKeys: [],
};

export default Search;
