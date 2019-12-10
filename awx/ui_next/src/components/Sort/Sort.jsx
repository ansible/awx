import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Button,
  ButtonVariant,
  Dropdown,
  DropdownPosition,
  DropdownToggle,
  DropdownItem,
  InputGroup,
} from '@patternfly/react-core';
import {
  SortAlphaDownIcon,
  SortAlphaUpIcon,
  SortNumericDownIcon,
  SortNumericUpIcon,
} from '@patternfly/react-icons';

import {
  parseQueryString
} from '@util/qs';
import { SortColumns, QSConfig } from '@types';

class Sort extends React.Component {
  constructor(props) {
    super(props);

    let sortKey;
    let sortOrder;
    let isNumeric;

    const { qsConfig, location } = this.props;
    const queryParams = parseQueryString(qsConfig, location.search);
    if (queryParams.order_by && queryParams.order_by.startsWith('-')) {
      sortKey = queryParams.order_by.substr(1);
      sortOrder = 'descending';
    } else if (queryParams.order_by) {
      sortKey = queryParams.order_by;
      sortOrder = 'ascending';
    }

    if (qsConfig.integerFields.filter(field => field === sortKey).length) {
      isNumeric = true;
    } else {
      isNumeric = false;
    }

    this.state = {
      isSortDropdownOpen: false,
      sortKey,
      sortOrder,
      isNumeric
    };

    this.handleDropdownToggle = this.handleDropdownToggle.bind(this);
    this.handleDropdownSelect = this.handleDropdownSelect.bind(this);
    this.handleSort = this.handleSort.bind(this);
  }

  handleDropdownToggle(isSortDropdownOpen) {
    this.setState({ isSortDropdownOpen });
  }

  handleDropdownSelect({ target }) {
    const { columns, onSort, qsConfig } = this.props;
    const { sortOrder } = this.state;
    const { innerText } = target;

    const [{ key: sortKey }] = columns.filter(
      ({ name }) => name === innerText
    );

    let isNumeric;

    if (qsConfig.integerFields.filter(field => field === sortKey).length) {
      isNumeric = true;
    } else {
      isNumeric = false;
    }

    this.setState({ isSortDropdownOpen: false, sortKey, isNumeric });
    onSort(sortKey, sortOrder);
  }

  handleSort() {
    const { onSort } = this.props;
    const { sortKey, sortOrder } = this.state;
    const newSortOrder = sortOrder === 'ascending' ? 'descending' : 'ascending';
    this.setState({ sortOrder: newSortOrder });
    onSort(sortKey, newSortOrder);
  }

  render() {
    const { up } = DropdownPosition;
    const { columns, i18n } = this.props;
    const { isSortDropdownOpen, sortKey, sortOrder, isNumeric } = this.state;
    const [{ name: sortedColumnName }] = columns.filter(
      ({ key }) => key === sortKey
    );

    const sortDropdownItems = columns
      .filter(({ key }) => key !== sortKey)
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
      <Fragment>
        {sortDropdownItems.length > 0 && (
          <InputGroup>
            <Dropdown
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
            <Button
              variant={ButtonVariant.control}
              aria-label={i18n._(t`Reverse Sort Order`)}
              onClick={this.handleSort}
            >
              <SortIcon />
            </Button>
          </InputGroup>
        )}
      </Fragment>
    );
  }
}

Sort.propTypes = {
  qsConfig: QSConfig.isRequired,
  columns: SortColumns.isRequired,
  onSort: PropTypes.func
};

Sort.defaultProps = {
  onSort: null
};

export default withI18n()(withRouter(Sort));
