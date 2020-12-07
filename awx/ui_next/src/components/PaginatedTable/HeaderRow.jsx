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

export default function HeaderRow({ qsConfig, defaultSortKey, children }) {
  const location = useLocation();
  const history = useHistory();

  const params = parseQueryString(qsConfig, location.search);

  const onSort = (key, order) => {
    const newParams = replaceParams(params, {
      order_by: order === 'asc' ? key : `-${key}`,
      page: null,
    });
    const encodedParams = encodeNonDefaultQueryString(qsConfig, newParams);
    history.push(
      encodedParams
        ? `${location.pathname}?${encodedParams}`
        : location.pathname
    );
  };

  const sortKey = params.order_by?.replace('-', '');
  const sortBy = {
    index: sortKey || defaultSortKey,
    direction: params.order_by?.startsWith('-') ? 'desc' : 'asc',
  };

  return (
    <Thead>
      <Tr>
        <Th />
        {React.Children.map(children, child =>
          React.cloneElement(child, {
            onSort,
            sortBy,
            columnIndex: child.props.sortKey,
          })
        )}
      </Tr>
    </Thead>
  );
}

export function HeaderCell({ sortKey, onSort, sortBy, columnIndex, children }) {
  const sort = sortKey
    ? {
        onSort: (event, key, order) => onSort(sortKey, order),
        sortBy,
        columnIndex,
      }
    : null;
  return <Th sort={sort}>{children}</Th>;
}
