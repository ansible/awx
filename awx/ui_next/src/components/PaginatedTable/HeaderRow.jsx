import 'styled-components/macro';
import React from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import { Thead, Tr, Th as PFTh } from '@patternfly/react-table';
import styled from 'styled-components';
import {
  encodeNonDefaultQueryString,
  parseQueryString,
  replaceParams,
} from '../../util/qs';

const Th = styled(PFTh)`
  --pf-c-table--cell--Overflow: initial;
`;

export default function HeaderRow({
  qsConfig,
  isExpandable,
  isSelectable,
  children,
}) {
  const location = useLocation();
  const history = useHistory();

  const params = parseQueryString(qsConfig, location.search);

  const onSort = (key, order) => {
    const newParams = replaceParams(params, {
      order_by: order === 'asc' ? key : `-${key}`,
      page: null,
    });
    const nonNamespacedParams = parseQueryString({}, history.location.search);
    const encodedParams = encodeNonDefaultQueryString(
      qsConfig,
      newParams,
      nonNamespacedParams
    );
    history.push(
      encodedParams
        ? `${location.pathname}?${encodedParams}`
        : location.pathname
    );
  };

  const sortKey = params.order_by?.replace('-', '');
  const sortBy = {
    index: sortKey || qsConfig.defaultParams?.order_by,
    direction: params.order_by?.startsWith('-') ? 'desc' : 'asc',
  };
  const idPrefix = `${qsConfig.namespace}-table-sort`;

  // empty first Th aligns with checkboxes in table rows
  return (
    <Thead>
      <Tr>
        {isExpandable && <Th />}
        {isSelectable && <Th />}
        {React.Children.map(
          children,
          child =>
            child &&
            React.cloneElement(child, {
              onSort,
              sortBy,
              columnIndex: child.props.sortKey,
              idPrefix,
            })
        )}
      </Tr>
    </Thead>
  );
}

HeaderRow.defaultProps = {
  isSelectable: true,
};

export function HeaderCell({
  sortKey,
  onSort,
  sortBy,
  columnIndex,
  idPrefix,
  className,
  alignRight,
  children,
}) {
  const sort = sortKey
    ? {
        onSort: (event, key, order) => onSort(sortKey, order),
        sortBy,
        columnIndex,
      }
    : null;
  return (
    <Th
      id={sortKey ? `${idPrefix}-${sortKey}` : null}
      className={className}
      sort={sort}
      css={alignRight ? 'text-align: right' : null}
    >
      {children}
    </Th>
  );
}
