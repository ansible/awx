import React from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Dropdown,
  DropdownPosition,
  DropdownToggle,
  DropdownItem,
  TextInput
} from '@patternfly/react-core';

class Search extends React.Component {
  constructor (props) {
    super(props);

    const { sortedColumnKey } = this.props;
    this.state = {
      isSearchDropdownOpen: false,
      searchKey: sortedColumnKey,
      searchValue: '',
    };

    this.handleSearchInputChange = this.handleSearchInputChange.bind(this);
    this.onSearchDropdownToggle = this.onSearchDropdownToggle.bind(this);
    this.onSearchDropdownSelect = this.onSearchDropdownSelect.bind(this);
    this.onSearch = this.onSearch.bind(this);
  }

  onSearchDropdownToggle (isSearchDropdownOpen) {
    this.setState({ isSearchDropdownOpen });
  }

  onSearchDropdownSelect ({ target }) {
    const { columns } = this.props;
    const { innerText } = target;

    const [{ key: searchKey }] = columns.filter(({ name }) => name === innerText);
    this.setState({ isSearchDropdownOpen: false, searchKey });
  }

  onSearch () {
    const { searchValue } = this.state;
    const { onSearch } = this.props;

    onSearch(searchValue);
  }

  handleSearchInputChange (searchValue) {
    this.setState({ searchValue });
  }

  render () {
    const { up } = DropdownPosition;
    const {
      columns
    } = this.props;
    const {
      isSearchDropdownOpen,
      searchKey,
      searchValue,
    } = this.state;

    const [{ name: searchColumnName }] = columns.filter(({ key }) => key === searchKey);

    const searchDropdownItems = columns
      .filter(({ key }) => key !== searchKey)
      .map(({ key, name }) => (
        <DropdownItem key={key} component="button">
          {name}
        </DropdownItem>
      ));

    return (
      <I18n>
        {({ i18n }) => (
          <div className="pf-c-input-group">
            <Dropdown
              className="searchKeyDropdown"
              onToggle={this.onSearchDropdownToggle}
              onSelect={this.onSearchDropdownSelect}
              direction={up}
              isOpen={isSearchDropdownOpen}
              toggle={(
                <DropdownToggle
                  onToggle={this.onSearchDropdownToggle}
                >
                  {searchColumnName}
                </DropdownToggle>
              )}
              dropdownItems={searchDropdownItems}
            />
            <TextInput
              type="search"
              aria-label="Search text input"
              value={searchValue}
              onChange={this.handleSearchInputChange}
              style={{ height: '30px' }}
            />
            <Button
              variant="tertiary"
              aria-label={i18n._(t`Search`)}
              onClick={this.onSearch}
            >
              <i className="fas fa-search" aria-hidden="true" />
            </Button>
          </div>
        )}
      </I18n>
    );
  }
}

Search.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  onSearch: PropTypes.func,
  sortedColumnKey: PropTypes.string,
};

Search.defaultProps = {
  onSearch: null,
  sortedColumnKey: 'name'
};

export default Search;
