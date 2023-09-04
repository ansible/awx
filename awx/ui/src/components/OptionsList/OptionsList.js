import React from 'react';
import {
  arrayOf,
  shape,
  bool,
  func,
  number,
  string,
  oneOfType,
} from 'prop-types';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { QSConfig, SearchColumns, SortColumns } from 'types';
import { SelectedList, DraggableSelectedList } from '../SelectedList';
import CheckboxListItem from '../CheckboxListItem';
import DataListToolbar from '../DataListToolbar';
import PaginatedTable, { HeaderCell, HeaderRow } from '../PaginatedTable';

const ModalList = styled.div`
  .pf-c-toolbar__content {
    padding: 0 !important;
  }
`;

function OptionsList({
  columns,
  contentError,
  deselectItem,
  displayKey,
  header,
  isLoading,
  isSelectedDraggable,
  multiple,
  name,
  optionCount,
  options,
  qsConfig,
  readOnly,
  relatedSearchableKeys,
  renderItemChip,
  searchColumns,
  searchableKeys,
  selectItem,
  sortColumns,
  sortSelectedItems,
  value,
}) {
  const buildHeaderRow = (
    <HeaderRow qsConfig={qsConfig}>
      {columns?.length > 0 ? (
        columns.map((col) => (
          <HeaderCell key={col.key} sortKey={col.key}>
            {col.name}
          </HeaderCell>
        ))
      ) : (
        <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
      )}
    </HeaderRow>
  );
  let selectionPreview = null;
  if (value.length > 0) {
    if (isSelectedDraggable) {
      selectionPreview = (
        <DraggableSelectedList
          onRemove={deselectItem}
          onRowDrag={sortSelectedItems}
          selected={value}
        />
      );
    } else {
      selectionPreview = (
        <SelectedList
          label={t`Selected`}
          selected={value}
          onRemove={(item) => deselectItem(item)}
          isReadOnly={readOnly}
          renderItemChip={renderItemChip}
          displayKey={displayKey}
        />
      );
    }
  }

  return (
    <ModalList>
      {selectionPreview}
      <PaginatedTable
        contentError={contentError}
        items={options}
        itemCount={optionCount}
        pluralizedItemName={header}
        qsConfig={qsConfig}
        toolbarSearchColumns={searchColumns}
        toolbarSortColumns={sortColumns}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        hasContentLoading={isLoading}
        headerRow={buildHeaderRow}
        onRowClick={selectItem}
        renderRow={(item, index) => (
          <CheckboxListItem
            key={item.id}
            rowIndex={index}
            itemId={item.id}
            name={multiple ? item[displayKey] : name}
            label={item[displayKey]}
            columns={columns}
            item={item}
            isSelected={value.some((i) => i.id === item.id)}
            onSelect={() => selectItem(item)}
            onDeselect={() => deselectItem(item)}
            isRadio={!multiple}
          />
        )}
        renderToolbar={(props) => <DataListToolbar {...props} fillWidth />}
        showPageSizeOptions={false}
      />
    </ModalList>
  );
}

const Item = shape({
  id: oneOfType([number, string]).isRequired,
  name: string.isRequired,
  url: string,
});
const InstanceItem = shape({
  id: oneOfType([number, string]).isRequired,
  hostname: string.isRequired,
  url: string,
});
OptionsList.propTypes = {
  deselectItem: func.isRequired,
  displayKey: string,
  isSelectedDraggable: bool,
  multiple: bool,
  optionCount: number.isRequired,
  options: oneOfType([arrayOf(Item), arrayOf(InstanceItem)]).isRequired,
  qsConfig: QSConfig.isRequired,
  renderItemChip: func,
  searchColumns: SearchColumns,
  selectItem: func.isRequired,
  sortColumns: SortColumns,
  value: oneOfType([arrayOf(Item), arrayOf(InstanceItem)]).isRequired,
};
OptionsList.defaultProps = {
  isSelectedDraggable: false,
  multiple: false,
  renderItemChip: null,
  searchColumns: [],
  sortColumns: [],
  displayKey: 'name',
};

export default OptionsList;
