import 'styled-components/macro';
import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { TableComposable, Tbody } from '@patternfly/react-table';

import { t } from '@lingui/macro';
import { useLocation, useHistory } from 'react-router-dom';

import { parseQueryString, updateQueryString } from 'util/qs';
import { QSConfig, SearchColumns, SearchableKeys } from 'types';
import ListHeader from '../ListHeader';
import ContentEmpty from '../ContentEmpty';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import Pagination from '../Pagination';
import DataListToolbar from '../DataListToolbar';
import LoadingSpinner from '../LoadingSpinner';

function PaginatedTable({
  contentError,
  hasContentLoading,
  emptyStateControls,
  items,
  itemCount,
  qsConfig,
  headerRow,
  renderRow,
  toolbarSearchColumns,
  toolbarSearchableKeys,
  toolbarRelatedSearchableKeys,
  pluralizedItemName,
  showPageSizeOptions,
  renderToolbar,
  emptyContentMessage,
  clearSelected,
  ouiaId,
}) {
  const { search, pathname } = useLocation();
  const history = useHistory();
  const location = useLocation();
  if (!pluralizedItemName) {
    pluralizedItemName = t`Items`;
  }

  useEffect(() => {
    clearSelected();
  }, [location.search, clearSelected]);

  const pushHistoryState = (qs) => {
    history.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const handleSetPage = (event, pageNumber) => {
    const qs = updateQueryString(qsConfig, search, {
      page: pageNumber,
    });
    pushHistoryState(qs);
  };

  const handleSetPageSize = (event, pageSize, page) => {
    const qs = updateQueryString(qsConfig, search, {
      page_size: pageSize,
      page,
    });
    pushHistoryState(qs);
  };

  const searchColumns = toolbarSearchColumns.length
    ? toolbarSearchColumns
    : [
        {
          name: t`Name`,
          key: 'name',
          isDefault: true,
        },
      ];
  const queryParams = parseQueryString(qsConfig, history.location.search);

  const dataListLabel = t`${pluralizedItemName} List`;
  const emptyContentTitle = t`No ${pluralizedItemName} Found `;

  let Content;
  if (hasContentLoading && items.length <= 0) {
    Content = <ContentLoading />;
  } else if (contentError) {
    Content = <ContentError error={contentError} />;
  } else if (items.length <= 0) {
    Content = (
      <ContentEmpty
        title={emptyContentTitle}
        message={
          emptyContentMessage ||
          t`Please add ${pluralizedItemName} to populate this list `
        }
      />
    );
  } else {
    Content = (
      <div css="overflow: auto">
        {hasContentLoading && <LoadingSpinner />}
        <TableComposable
          aria-label={dataListLabel}
          ouiaId={ouiaId || `paginated-table-${pluralizedItemName}`}
        >
          {headerRow}
          <Tbody>{items.map(renderRow)}</Tbody>
        </TableComposable>
      </div>
    );
  }

  const ToolbarPagination = (
    <Pagination
      isCompact
      dropDirection="down"
      itemCount={itemCount}
      page={queryParams.page || 1}
      perPage={queryParams.page_size}
      perPageOptions={
        showPageSizeOptions
          ? [
              { title: '5', value: 5 },
              { title: '10', value: 10 },
              { title: '20', value: 20 },
              { title: '50', value: 50 },
            ]
          : []
      }
      onSetPage={handleSetPage}
      onPerPageSelect={handleSetPageSize}
      ouiaId="top-pagination"
    />
  );

  return (
    <>
      <ListHeader
        emptyStateControls={emptyStateControls}
        itemCount={itemCount}
        pagination={ToolbarPagination}
        qsConfig={qsConfig}
        relatedSearchableKeys={toolbarRelatedSearchableKeys}
        renderToolbar={renderToolbar}
        searchColumns={searchColumns}
        searchableKeys={toolbarSearchableKeys}
      />
      {Content}
      {items.length ? (
        <Pagination
          variant="bottom"
          itemCount={itemCount}
          page={queryParams.page || 1}
          perPage={queryParams.page_size}
          perPageOptions={
            showPageSizeOptions
              ? [
                  { title: '5', value: 5 },
                  { title: '10', value: 10 },
                  { title: '20', value: 20 },
                  { title: '50', value: 50 },
                ]
              : []
          }
          onSetPage={handleSetPage}
          onPerPageSelect={handleSetPageSize}
          ouiaId="bottom-pagination"
        />
      ) : null}
    </>
  );
}

const Item = PropTypes.shape({
  id: PropTypes.number.isRequired,
  url: PropTypes.string.isRequired,
  name: PropTypes.string,
});

PaginatedTable.propTypes = {
  items: PropTypes.arrayOf(Item).isRequired,
  itemCount: PropTypes.number.isRequired,
  pluralizedItemName: PropTypes.string,
  qsConfig: QSConfig.isRequired,
  renderRow: PropTypes.func.isRequired,
  toolbarSearchColumns: SearchColumns,
  toolbarSearchableKeys: SearchableKeys,
  toolbarRelatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  showPageSizeOptions: PropTypes.bool,
  renderToolbar: PropTypes.func,
  hasContentLoading: PropTypes.bool,
  contentError: PropTypes.shape(),
  clearSelected: PropTypes.func,
  ouiaId: PropTypes.string,
};

PaginatedTable.defaultProps = {
  hasContentLoading: false,
  contentError: null,
  toolbarSearchColumns: [],
  toolbarSearchableKeys: [],
  toolbarRelatedSearchableKeys: [],
  pluralizedItemName: null,
  showPageSizeOptions: true,
  renderToolbar: (props) => <DataListToolbar {...props} />,
  ouiaId: null,
  clearSelected: () => {},
};

export { PaginatedTable as _PaginatedTable };
export default PaginatedTable;
