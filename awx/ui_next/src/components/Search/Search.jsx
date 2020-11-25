import 'styled-components/macro';
import React, { Fragment, useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter } from 'react-router-dom';
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
import { parseQueryString } from '../../util/qs';
import { QSConfig, SearchColumns } from '../../types';
import AdvancedSearch from './AdvancedSearch';

const NoOptionDropdown = styled.div`
  align-self: stretch;
  border: 1px solid var(--pf-global--BorderColor--300);
  padding: 5px 15px;
  white-space: nowrap;
  border-bottom-color: var(--pf-global--BorderColor--200);
`;

function Search({
  columns,
  i18n,
  onSearch,
  onReplaceSearch,
  onRemove,
  qsConfig,
  location,
  searchableKeys,
  relatedSearchableKeys,
  onShowAdvancedSearch,
}) {
  const [isSearchDropdownOpen, setIsSearchDropdownOpen] = useState(false);
  const [searchKey, setSearchKey] = useState(
    (() => {
      const defaultColumn = columns.filter(col => col.isDefault);

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

  const handleDropdownSelect = ({ target }) => {
    const { key: actualSearchKey } = columns.find(
      ({ name }) => name === target.innerText
    );
    onShowAdvancedSearch(actualSearchKey === 'advanced');
    setIsFilterDropdownOpen(false);
    setSearchKey(actualSearchKey);
  };

  const handleSearch = e => {
    // keeps page from fully reloading
    e.preventDefault();

    if (searchValue) {
      onSearch(searchKey, searchValue);
      setSearchValue('');
    }
  };

  const handleTextKeyDown = e => {
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

  const filterDefaultParams = (paramsArr, config) => {
    const defaultParamsKeys = Object.keys(config.defaultParams || {});
    return paramsArr.filter(key => defaultParamsKeys.indexOf(key) === -1);
  };

  const getLabelFromValue = (value, colKey) => {
    let label = value;
    const currentSearchColumn = columns.find(({ key }) => key === colKey);
    if (currentSearchColumn?.options?.length) {
      [, label] = currentSearchColumn.options.find(
        ([optVal]) => optVal === value
      );
    } else if (currentSearchColumn?.booleanLabels) {
      label = currentSearchColumn.booleanLabels[value];
    }
    return (label || colKey).toString();
  };

  const getChipsByKey = () => {
    const queryParams = parseQueryString(qsConfig, location.search);

    const queryParamsByKey = {};
    columns.forEach(({ name, key }) => {
      queryParamsByKey[key] = { key, label: name, chips: [] };
    });
    const nonDefaultParams = filterDefaultParams(
      Object.keys(queryParams || {}),
      qsConfig
    );

    nonDefaultParams.forEach(key => {
      const columnKey = key;
      const label = columns.filter(
        ({ key: keyToCheck }) => columnKey === keyToCheck
      ).length
        ? `${
            columns.find(({ key: keyToCheck }) => columnKey === keyToCheck).name
          } (${key})`
        : columnKey;

      queryParamsByKey[columnKey] = { key, label, chips: [] };

      if (Array.isArray(queryParams[key])) {
        queryParams[key].forEach(val =>
          queryParamsByKey[columnKey].chips.push({
            key: `${key}:${val}`,
            node: getLabelFromValue(val, columnKey),
          })
        );
      } else {
        queryParamsByKey[columnKey].chips.push({
          key: `${key}:${queryParams[key]}`,
          node: getLabelFromValue(queryParams[key], columnKey),
        });
      }
    });
    return queryParamsByKey;
  };

  const chipsByKey = getChipsByKey();

  const { name: searchColumnName } = columns.find(
    ({ key }) => key === searchKey
  );

  const searchOptions = columns
    .filter(({ key }) => key !== searchKey)
    .map(({ key, name }) => (
      <SelectOption key={key} value={name}>
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
            aria-label={i18n._(t`Simple key select`)}
            onToggle={setIsSearchDropdownOpen}
            onSelect={handleDropdownSelect}
            selections={searchColumnName}
            isOpen={isSearchDropdownOpen}
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
            />
          )) ||
            (options && (
              <Fragment>
                <Select
                  variant={SelectVariant.checkbox}
                  aria-label={name}
                  onToggle={setIsFilterDropdownOpen}
                  onSelect={(event, selection) =>
                    handleFilterDropdownSelect(key, event, selection)
                  }
                  selections={chipsByKey[key].chips.map(chip => {
                    const [, ...value] = chip.key.split(':');
                    return value.join(':');
                  })}
                  isOpen={isFilterDropdownOpen}
                  placeholderText={`Filter By ${name}`}
                >
                  {options.map(([optionKey, optionLabel]) => (
                    <SelectOption key={optionKey} value={optionKey}>
                      {optionLabel}
                    </SelectOption>
                  ))}
                </Select>
              </Fragment>
            )) ||
            (isBoolean && (
              <Select
                aria-label={name}
                onToggle={setIsFilterDropdownOpen}
                onSelect={(event, selection) => onReplaceSearch(key, selection)}
                selections={chipsByKey[key].chips[0]?.label}
                isOpen={isFilterDropdownOpen}
                placeholderText={`Filter By ${name}`}
              >
                <SelectOption key="true" value="true">
                  {booleanLabels.true || i18n._(t`Yes`)}
                </SelectOption>
                <SelectOption key="false" value="false">
                  {booleanLabels.false || i18n._(t`No`)}
                </SelectOption>
              </Select>
            )) || (
              <InputGroup>
                {/* TODO: add support for dates:
          qsConfig.dateFields.filter(field => field === key).length && "date" */}
                <TextInput
                  type={
                    (qsConfig.integerFields.find(
                      field => field === searchKey
                    ) &&
                      'number') ||
                    'search'
                  }
                  aria-label={i18n._(t`Search text input`)}
                  value={searchValue}
                  onChange={setSearchValue}
                  onKeyDown={handleTextKeyDown}
                />
                <div css={!searchValue && `cursor:not-allowed`}>
                  <Button
                    variant={ButtonVariant.control}
                    isDisabled={!searchValue}
                    aria-label={i18n._(t`Search submit button`)}
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
        .filter(val => chipsByKey[val].chips.length > 0)
        .filter(val => columns.map(val2 => val2.key).indexOf(val) === -1)
        .map(leftoverKey => (
          <ToolbarFilter
            chips={chipsByKey[leftoverKey] ? chipsByKey[leftoverKey].chips : []}
            deleteChip={(unusedKey, chip) => {
              const [columnKey, ...value] = chip.key.split(':');
              onRemove(columnKey, value.join(':'));
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
};

Search.defaultProps = {
  onSearch: null,
  onRemove: null,
};

export default withI18n()(withRouter(Search));
