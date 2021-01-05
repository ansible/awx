import React, { Fragment, useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { useLocation, withRouter } from 'react-router-dom';
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
  SortAlphaDownAltIcon,
  SortNumericDownIcon,
  SortNumericDownAltIcon,
} from '@patternfly/react-icons';

import styled from 'styled-components';
import { parseQueryString } from '../../util/qs';
import { SortColumns, QSConfig } from '../../types';

const NoOptionDropdown = styled.div`
  align-self: stretch;
  border: 1px solid var(--pf-global--BorderColor--300);
  padding: 5px 15px;
  white-space: nowrap;
  border-bottom-color: var(--pf-global--BorderColor--200);
`;

function Sort({ columns, qsConfig, onSort, i18n }) {
  const location = useLocation();
  const [isSortDropdownOpen, setIsSortDropdownOpen] = useState(false);

  let sortKey;
  let sortOrder;
  let isNumeric;

  const queryParams = parseQueryString(qsConfig, location.search);
  if (queryParams.order_by && queryParams.order_by.startsWith('-')) {
    sortKey = queryParams.order_by.substr(1);
    sortOrder = 'descending';
  } else if (queryParams.order_by) {
    sortKey = queryParams.order_by;
    sortOrder = 'ascending';
  }

  if (qsConfig.integerFields.find(field => field === sortKey)) {
    isNumeric = true;
  } else {
    isNumeric = false;
  }

  const handleDropdownToggle = isOpen => {
    setIsSortDropdownOpen(isOpen);
  };

  const handleDropdownSelect = ({ target }) => {
    const { innerText } = target;

    const [{ key }] = columns.filter(({ name }) => name === innerText);
    sortKey = key;
    if (qsConfig.integerFields.find(field => field === key)) {
      isNumeric = true;
    } else {
      isNumeric = false;
    }

    setIsSortDropdownOpen(false);
    onSort(sortKey, sortOrder);
  };

  const handleSort = () => {
    onSort(sortKey, sortOrder === 'ascending' ? 'descending' : 'ascending');
  };

  const { up } = DropdownPosition;

  const defaultSortedColumn = columns.find(({ key }) => key === sortKey);

  if (!defaultSortedColumn) {
    throw new Error(
      'sortKey must match one of the column keys, check the sortColumns prop passed to <Sort />'
    );
  }

  const sortedColumnName = defaultSortedColumn?.name;

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
      sortOrder === 'ascending' ? SortNumericDownIcon : SortNumericDownAltIcon;
  } else {
    SortIcon =
      sortOrder === 'ascending' ? SortAlphaDownIcon : SortAlphaDownAltIcon;
  }
  return (
    <Fragment>
      {sortedColumnName && (
        <InputGroup>
          {(sortDropdownItems.length > 0 && (
            <Dropdown
              onToggle={handleDropdownToggle}
              onSelect={handleDropdownSelect}
              direction={up}
              isOpen={isSortDropdownOpen}
              toggle={
                <DropdownToggle id="awx-sort" onToggle={handleDropdownToggle}>
                  {sortedColumnName}
                </DropdownToggle>
              }
              dropdownItems={sortDropdownItems}
            />
          )) || <NoOptionDropdown>{sortedColumnName}</NoOptionDropdown>}

          <Button
            variant={ButtonVariant.control}
            aria-label={i18n._(t`Sort`)}
            onClick={handleSort}
          >
            <SortIcon />
          </Button>
        </InputGroup>
      )}
    </Fragment>
  );
}

Sort.propTypes = {
  qsConfig: QSConfig.isRequired,
  columns: SortColumns.isRequired,
  onSort: PropTypes.func,
};

Sort.defaultProps = {
  onSort: null,
};

export default withI18n()(withRouter(Sort));
