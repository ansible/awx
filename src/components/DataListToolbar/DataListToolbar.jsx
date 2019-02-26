import React from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Checkbox,
  Dropdown,
  DropdownPosition,
  DropdownToggle,
  DropdownItem,
  Level,
  LevelItem,
  TextInput,
  Toolbar,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import {
  BarsIcon,
  EqualsIcon,
  SortAlphaDownIcon,
  SortAlphaUpIcon,
  SortNumericDownIcon,
  SortNumericUpIcon,
  TrashAltIcon,
  PlusIcon,
} from '@patternfly/react-icons';
import {
  Link
} from 'react-router-dom';

import Tooltip from '../Tooltip';
import VerticalSeparator from '../VerticalSeparator';

const flexGrowStyling = {
  flexGrow: '1'
};

const ToolbarActiveStyle = {
  backgroundColor: 'rgb(0, 123, 186)',
  color: 'white',
  padding: '0 5px',
};

class DataListToolbar extends React.Component {
  constructor (props) {
    super(props);

    const { sortedColumnKey } = this.props;
    this.state = {
      isSearchDropdownOpen: false,
      isSortDropdownOpen: false,
      searchKey: sortedColumnKey,
      searchValue: '',
    };

    this.handleSearchInputChange = this.handleSearchInputChange.bind(this);
    this.onSortDropdownToggle = this.onSortDropdownToggle.bind(this);
    this.onSortDropdownSelect = this.onSortDropdownSelect.bind(this);
    this.onSearchDropdownToggle = this.onSearchDropdownToggle.bind(this);
    this.onSearchDropdownSelect = this.onSearchDropdownSelect.bind(this);
    this.onSearch = this.onSearch.bind(this);
    this.onSort = this.onSort.bind(this);
    this.onExpand = this.onExpand.bind(this);
    this.onCompact = this.onCompact.bind(this);
  }

  onExpand () {
    const { onExpand } = this.props;
    onExpand();
  }

  onCompact () {
    const { onCompact } = this.props;
    onCompact();
  }

  onSortDropdownToggle (isSortDropdownOpen) {
    this.setState({ isSortDropdownOpen });
  }

  onSortDropdownSelect ({ target }) {
    const { columns, onSort, sortOrder } = this.props;
    const { innerText } = target;

    const [{ key: searchKey }] = columns.filter(({ name }) => name === innerText);

    this.setState({ isSortDropdownOpen: false });
    onSort(searchKey, sortOrder);
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

  onSort () {
    const { onSort, sortedColumnKey, sortOrder } = this.props;
    const newSortOrder = sortOrder === 'ascending' ? 'descending' : 'ascending';

    onSort(sortedColumnKey, newSortOrder);
  }

  handleSearchInputChange (searchValue) {
    this.setState({ searchValue });
  }

  render () {
    const { up } = DropdownPosition;
    const {
      columns,
      isAllSelected,
      onSelectAll,
      sortedColumnKey,
      sortOrder,
      addUrl,
      showExpandCollapse,
      showDelete,
      showSelectAll,
      isLookup,
      isCompact,
    } = this.props;
    const {
      isSearchDropdownOpen,
      isSortDropdownOpen,
      searchKey,
      searchValue,
    } = this.state;

    const [{ name: searchColumnName }] = columns.filter(({ key }) => key === searchKey);
    const [{ name: sortedColumnName, isNumeric }] = columns
      .filter(({ key }) => key === sortedColumnKey);

    const searchDropdownItems = columns
      .filter(({ key }) => key !== searchKey)
      .map(({ key, name }) => (
        <DropdownItem key={key} component="button">
          {name}
        </DropdownItem>
      ));

    const sortDropdownItems = columns
      .filter(({ key, isSortable }) => isSortable && key !== sortedColumnKey)
      .map(({ key, name }) => (
        <DropdownItem key={key} component="button">
          {name}
        </DropdownItem>
      ));

    let SortIcon;
    if (isNumeric) {
      SortIcon = sortOrder === 'ascending' ? SortNumericUpIcon : SortNumericDownIcon;
    } else {
      SortIcon = sortOrder === 'ascending' ? SortAlphaUpIcon : SortAlphaDownIcon;
    }

    return (
      <I18n>
        {({ i18n }) => (
          <div className="awx-toolbar">
            <Level>
              <LevelItem style={{ display: 'flex', flexBasis: '700px' }}>
                <Toolbar style={{ marginLeft: isLookup ? '0px' : '20px', flexGrow: '1' }}>
                  { showSelectAll && (
                    <ToolbarGroup>
                      <ToolbarItem>
                        <Checkbox
                          checked={isAllSelected}
                          onChange={onSelectAll}
                          aria-label={i18n._(t`Select all`)}
                          id="select-all"
                        />
                      </ToolbarItem>
                      <VerticalSeparator />
                    </ToolbarGroup>
                  )}
                  <ToolbarGroup style={flexGrowStyling}>
                    <ToolbarItem style={flexGrowStyling}>
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
                          aria-label={i18n._(t`Search text input`)}
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
                    </ToolbarItem>
                    <VerticalSeparator />
                  </ToolbarGroup>
                  <ToolbarGroup
                    className="sortDropdownGroup"
                  >
                    { sortDropdownItems.length > 1 && (
                      <ToolbarItem>
                        <Dropdown
                          onToggle={this.onSortDropdownToggle}
                          onSelect={this.onSortDropdownSelect}
                          direction={up}
                          isOpen={isSortDropdownOpen}
                          toggle={(
                            <DropdownToggle
                              onToggle={this.onSortDropdownToggle}
                            >
                              {sortedColumnName}
                            </DropdownToggle>
                          )}
                          dropdownItems={sortDropdownItems}
                        />
                      </ToolbarItem>
                    )}
                    <ToolbarItem>
                      <Button
                        onClick={this.onSort}
                        variant="plain"
                        aria-label={i18n._(t`Sort`)}
                      >
                        <SortIcon />
                      </Button>
                    </ToolbarItem>
                    { (showExpandCollapse || showDelete || addUrl) && (
                      <VerticalSeparator />
                    )}
                  </ToolbarGroup>
                  {showExpandCollapse && (
                    <ToolbarGroup>
                      <ToolbarItem>
                        <Button
                          variant="plain"
                          aria-label={i18n._(t`Expand`)}
                          onClick={this.onExpand}
                          style={!isCompact ? ToolbarActiveStyle : null}
                        >
                          <EqualsIcon />
                        </Button>
                      </ToolbarItem>
                      <ToolbarItem>
                        <Button
                          variant="plain"
                          aria-label={i18n._(t`Collapse`)}
                          onClick={this.onCompact}
                          style={isCompact ? ToolbarActiveStyle : null}
                        >
                          <BarsIcon />
                        </Button>
                      </ToolbarItem>
                      { (showDelete || addUrl) && (
                        <VerticalSeparator />
                      )}
                    </ToolbarGroup>
                  )}
                </Toolbar>
              </LevelItem>
              <LevelItem>
                { showDelete && (
                  <Tooltip
                    message={i18n._(t`Delete`)}
                    position="top"
                  >
                    <Button
                      variant="plain"
                      aria-label={i18n._(t`Delete`)}
                    >
                      <TrashAltIcon />
                    </Button>
                  </Tooltip>
                )}
                {addUrl && (
                  <Link to={addUrl}>
                    <Button
                      variant="primary"
                      aria-label={i18n._(t`Add`)}
                    >
                      <PlusIcon />
                    </Button>
                  </Link>
                )}
              </LevelItem>
            </Level>
          </div>
        )}
      </I18n>
    );
  }
}

DataListToolbar.propTypes = {
  addUrl: PropTypes.string,
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  isAllSelected: PropTypes.bool,
  onSearch: PropTypes.func,
  onSelectAll: PropTypes.func,
  onSort: PropTypes.func,
  showDelete: PropTypes.bool,
  showExpandCollapse: PropTypes.bool,
  showSelectAll: PropTypes.bool,
  sortOrder: PropTypes.string,
  sortedColumnKey: PropTypes.string,
};

DataListToolbar.defaultProps = {
  addUrl: null,
  onSearch: null,
  onSelectAll: null,
  onSort: null,
  showDelete: false,
  showExpandCollapse: false,
  showSelectAll: false,
  sortOrder: 'ascending',
  sortedColumnKey: 'name',
  isAllSelected: false,
};

export default DataListToolbar;
