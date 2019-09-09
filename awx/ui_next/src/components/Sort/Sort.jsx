import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Dropdown as PFDropdown,
  DropdownPosition,
  DropdownToggle,
  DropdownItem,
  Tooltip,
} from '@patternfly/react-core';
import {
  SortAlphaDownIcon,
  SortAlphaUpIcon,
  SortNumericDownIcon,
  SortNumericUpIcon,
} from '@patternfly/react-icons';

import styled from 'styled-components';

const Dropdown = styled(PFDropdown)`
  &&& {
    > button {
      min-height: 30px;
      min-width: 70px;
      height: 30px;
      padding: 0 10px;
      margin: 0px;

      > span {
        /* text element within dropdown */
        width: auto;
      }

      > svg {
        /* caret icon */
        margin: 0px;
        padding-top: 3px;
        padding-left: 3px;
      }
    }
  }
`;

const IconWrapper = styled.span`
  > svg {
    font-size: 18px;
  }
`;

const SortButton = styled(Button)`
  padding: 5px 8px;
  margin-top: 3px;

  &:hover {
    background-color: #0166cc;
    color: white;
  }
`;

const SortBy = styled.span`
  margin-right: 15px;
  font-size: var(--pf-global--FontSize--md);
`;

class Sort extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      isSortDropdownOpen: false,
    };

    this.handleDropdownToggle = this.handleDropdownToggle.bind(this);
    this.handleDropdownSelect = this.handleDropdownSelect.bind(this);
    this.handleSort = this.handleSort.bind(this);
  }

  handleDropdownToggle(isSortDropdownOpen) {
    this.setState({ isSortDropdownOpen });
  }

  handleDropdownSelect({ target }) {
    const { columns, onSort, sortOrder } = this.props;
    const { innerText } = target;

    const [{ key: searchKey }] = columns.filter(
      ({ name }) => name === innerText
    );

    this.setState({ isSortDropdownOpen: false });
    onSort(searchKey, sortOrder);
  }

  handleSort() {
    const { onSort, sortedColumnKey, sortOrder } = this.props;
    const newSortOrder = sortOrder === 'ascending' ? 'descending' : 'ascending';

    onSort(sortedColumnKey, newSortOrder);
  }

  render() {
    const { up } = DropdownPosition;
    const { columns, sortedColumnKey, sortOrder, i18n } = this.props;
    const { isSortDropdownOpen } = this.state;
    const [{ name: sortedColumnName, isNumeric }] = columns.filter(
      ({ key }) => key === sortedColumnKey
    );

    const sortDropdownItems = columns
      .filter(({ key, isSortable }) => isSortable && key !== sortedColumnKey)
      .map(({ key, name }) => (
        <DropdownItem key={key} component="button">
          {name}
        </DropdownItem>
      ));

    let SortIcon;
    if (isNumeric) {
      SortIcon =
        sortOrder === 'ascending' ? SortNumericUpIcon : SortNumericDownIcon;
    } else {
      SortIcon =
        sortOrder === 'ascending' ? SortAlphaUpIcon : SortAlphaDownIcon;
    }

    return (
      <React.Fragment>
        {sortDropdownItems.length > 1 && (
          <React.Fragment>
            <SortBy>{i18n._(t`Sort By`)}</SortBy>
            <Dropdown
              style={{ marginRight: '10px' }}
              onToggle={this.handleDropdownToggle}
              onSelect={this.handleDropdownSelect}
              direction={up}
              isOpen={isSortDropdownOpen}
              toggle={
                <DropdownToggle
                  id="awx-sort"
                  onToggle={this.handleDropdownToggle}
                >
                  {sortedColumnName}
                </DropdownToggle>
              }
              dropdownItems={sortDropdownItems}
            />
          </React.Fragment>
        )}
        <Tooltip
          content={<div>{i18n._(t`Reverse Sort Order`)}</div>}
          position="top"
        >
          <SortButton
            onClick={this.handleSort}
            variant="plain"
            aria-label={i18n._(t`Sort`)}
          >
            <IconWrapper>
              <SortIcon style={{ verticalAlign: '-0.225em' }} />
            </IconWrapper>
          </SortButton>
        </Tooltip>
      </React.Fragment>
    );
  }
}

Sort.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  onSort: PropTypes.func,
  sortOrder: PropTypes.string,
  sortedColumnKey: PropTypes.string,
};

Sort.defaultProps = {
  onSort: null,
  sortOrder: 'ascending',
  sortedColumnKey: 'name',
};

export default withI18n()(Sort);
