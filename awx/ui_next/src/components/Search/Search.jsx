import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter } from 'react-router-dom';
import {
  Button,
  ButtonVariant,
  Dropdown,
  DropdownPosition,
  DropdownToggle,
  DropdownItem,
  InputGroup,
  Select,
  SelectOption,
  SelectVariant,
  TextInput,
} from '@patternfly/react-core';
import {
  DataToolbarGroup,
  DataToolbarItem,
  DataToolbarFilter,
} from '@patternfly/react-core/dist/umd/experimental';
import { SearchIcon } from '@patternfly/react-icons';
import { parseQueryString } from '@util/qs';
import { QSConfig, SearchColumns } from '@types';
import styled from 'styled-components';

const NoOptionDropdown = styled.div`
  align-self: stretch;
  border: 1px solid var(--pf-global--BorderColor--300);
  padding: 5px 15px;
  white-space: nowrap;
  border-bottom-color: var(--pf-global--BorderColor--200);
`;

class Search extends React.Component {
  constructor(props) {
    super(props);

    const { columns } = this.props;

    this.state = {
      isSearchDropdownOpen: false,
      searchKey: columns.find(col => col.isDefault).key,
      searchValue: '',
      isFilterDropdownOpen: false,
    };

    this.handleSearchInputChange = this.handleSearchInputChange.bind(this);
    this.handleDropdownToggle = this.handleDropdownToggle.bind(this);
    this.handleDropdownSelect = this.handleDropdownSelect.bind(this);
    this.handleSearch = this.handleSearch.bind(this);
    this.handleTextKeyDown = this.handleTextKeyDown.bind(this);
    this.handleFilterDropdownToggle = this.handleFilterDropdownToggle.bind(
      this
    );
    this.handleFilterDropdownSelect = this.handleFilterDropdownSelect.bind(
      this
    );
    this.handleFilterBooleanSelect = this.handleFilterBooleanSelect.bind(this);
  }

  handleDropdownToggle(isSearchDropdownOpen) {
    this.setState({ isSearchDropdownOpen });
  }

  handleDropdownSelect({ target }) {
    const { columns } = this.props;
    const { innerText } = target;

    const { key: searchKey } = columns.find(({ name }) => name === innerText);
    this.setState({ isSearchDropdownOpen: false, searchKey });
  }

  handleSearch(e) {
    // keeps page from fully reloading
    e.preventDefault();

    const { searchKey, searchValue } = this.state;
    const { onSearch, qsConfig } = this.props;

    const isNonStringField =
      qsConfig.integerFields.find(field => field === searchKey) ||
      qsConfig.dateFields.find(field => field === searchKey);

    const actualSearchKey = isNonStringField
      ? searchKey
      : `${searchKey}__icontains`;

    onSearch(actualSearchKey, searchValue);

    this.setState({ searchValue: '' });
  }

  handleSearchInputChange(searchValue) {
    this.setState({ searchValue });
  }

  handleTextKeyDown(e) {
    if (e.key && e.key === 'Enter') {
      this.handleSearch(e);
    }
  }

  handleFilterDropdownToggle(isFilterDropdownOpen) {
    this.setState({ isFilterDropdownOpen });
  }

  handleFilterDropdownSelect(key, event, actualValue) {
    const { onSearch, onRemove } = this.props;

    if (event.target.checked) {
      onSearch(`or__${key}`, actualValue);
    } else {
      onRemove(`or__${key}`, actualValue);
    }
  }

  handleFilterBooleanSelect(key, selection) {
    const { onReplaceSearch } = this.props;
    onReplaceSearch(key, selection);
  }

  render() {
    const { up } = DropdownPosition;
    const { columns, i18n, onRemove, qsConfig, location } = this.props;
    const {
      isSearchDropdownOpen,
      searchKey,
      searchValue,
      isFilterDropdownOpen,
    } = this.state;
    const { name: searchColumnName } = columns.find(
      ({ key }) => key === searchKey
    );

    const searchDropdownItems = columns
      .filter(({ key }) => key !== searchKey)
      .map(({ key, name }) => (
        <DropdownItem key={key} component="button">
          {name}
        </DropdownItem>
      ));

    const filterDefaultParams = (paramsArr, config) => {
      const defaultParamsKeys = Object.keys(config.defaultParams || {});
      return paramsArr.filter(key => defaultParamsKeys.indexOf(key) === -1);
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
        const columnKey = key.replace('__icontains', '').replace('or__', '');
        const label = columns.filter(
          ({ key: keyToCheck }) => columnKey === keyToCheck
        ).length
          ? columns.filter(({ key: keyToCheck }) => columnKey === keyToCheck)[0]
              .name
          : columnKey;

        queryParamsByKey[columnKey] = { key, label, chips: [] };

        if (Array.isArray(queryParams[key])) {
          queryParams[key].forEach(val =>
            queryParamsByKey[columnKey].chips.push(val.toString())
          );
        } else {
          queryParamsByKey[columnKey].chips.push(queryParams[key].toString());
        }
      });

      return queryParamsByKey;
    };

    const chipsByKey = getChipsByKey();

    return (
      <DataToolbarGroup variant="filter-group">
        <DataToolbarItem>
          {searchDropdownItems.length > 0 ? (
            <Dropdown
              onToggle={this.handleDropdownToggle}
              onSelect={this.handleDropdownSelect}
              direction={up}
              toggle={
                <DropdownToggle
                  id="awx-search"
                  onToggle={this.handleDropdownToggle}
                  style={{ width: '100%' }}
                >
                  {searchColumnName}
                </DropdownToggle>
              }
              isOpen={isSearchDropdownOpen}
              dropdownItems={searchDropdownItems}
            />
          ) : (
            <NoOptionDropdown>{searchColumnName}</NoOptionDropdown>
          )}
        </DataToolbarItem>
        {columns.map(
          ({ key, name, options, isBoolean, booleanLabels = {} }) => (
            <DataToolbarFilter
              chips={chipsByKey[key] ? chipsByKey[key].chips : []}
              deleteChip={(unusedKey, val) => {
                onRemove(chipsByKey[key].key, val);
              }}
              categoryName={chipsByKey[key] ? chipsByKey[key].label : key}
              key={key}
              showToolbarItem={searchKey === key}
            >
              {(options && (
                <Fragment>
                  <Select
                    variant={SelectVariant.checkbox}
                    aria-label={name}
                    onToggle={this.handleFilterDropdownToggle}
                    onSelect={(event, selection) =>
                      this.handleFilterDropdownSelect(key, event, selection)
                    }
                    selections={chipsByKey[key].chips}
                    isExpanded={isFilterDropdownOpen}
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
                    onToggle={this.handleFilterDropdownToggle}
                    onSelect={(event, selection) =>
                      this.handleFilterBooleanSelect(key, selection)
                    }
                    selections={chipsByKey[key].chips[0]}
                    isExpanded={isFilterDropdownOpen}
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
                      onChange={this.handleSearchInputChange}
                      onKeyDown={this.handleTextKeyDown}
                    />
                    <Button
                      variant={ButtonVariant.control}
                      aria-label={i18n._(t`Search submit button`)}
                      onClick={this.handleSearch}
                    >
                      <SearchIcon />
                    </Button>
                  </InputGroup>
                )}
            </DataToolbarFilter>
          )
        )}
      </DataToolbarGroup>
    );
  }
}

Search.propTypes = {
  qsConfig: QSConfig.isRequired,
  columns: SearchColumns.isRequired,
  onSearch: PropTypes.func,
  onRemove: PropTypes.func,
};

Search.defaultProps = {
  onSearch: null,
  onRemove: null,
};

export default withI18n()(withRouter(Search));
