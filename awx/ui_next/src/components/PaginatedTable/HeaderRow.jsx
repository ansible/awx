import React from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import { Thead, Tr, Th } from '@patternfly/react-table';
import {
  encodeNonDefaultQueryString,
  parseQueryString,
  replaceParams,
} from '../../util/qs';

export default function HeaderRow({
  handleSelectAll,
  isAllSelected,
  qsConfig,
  defaultSortKey,
  children,
}) {
  const location = useLocation();
  const history = useHistory();

  const params = parseQueryString(qsConfig, location.search);

  // TODO: asc vs desc -- correct for both alpha & numeric sorting?
  const onSort = (key, order) => {
    console.log({ key, order });
    const newParams = replaceParams(params, {
      order_by: order === 'desc' ? key : `-${key}`,
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
    direction: params.order_by?.startsWith('-') ? 'asc' : 'desc',
  };

  return (
    <Thead>
      <Tr>
        <Th
          select={{
            onSelect: handleSelectAll,
            isSelected: isAllSelected,
          }}
        />
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
