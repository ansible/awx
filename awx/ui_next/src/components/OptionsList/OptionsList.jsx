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
import SelectedList from '../SelectedList';
import CheckboxListItem from '../CheckboxListItem';
import DataListToolbar from '../DataListToolbar';
import { QSConfig, SearchColumns, SortColumns } from '../../types';
import PaginatedTable, { HeaderCell, HeaderRow } from '../PaginatedTable';

const ModalList = styled.div`
  .pf-c-toolbar__content {
    padding: 0 !important;
  }
`;

function OptionsList({
  value,
  contentError,
  options,
  optionCount,
  searchColumns,
  sortColumns,
  searchableKeys,
  relatedSearchableKeys,
  multiple,
  header,
  name,
  qsConfig,
  readOnly,
  selectItem,
  deselectItem,
  renderItemChip,
  isLoading,
  displayKey,
}) {
  return (
    <ModalList>
      {value.length > 0 && (
        <SelectedList
          label={t`Selected`}
          selected={value}
          onRemove={item => deselectItem(item)}
          isReadOnly={readOnly}
          renderItemChip={renderItemChip}
          displayKey={displayKey}
        />
      )}
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
        headerRow={
          <HeaderRow qsConfig={qsConfig}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
          </HeaderRow>
        }
        onRowClick={selectItem}
        renderRow={(item, index) => (
          <CheckboxListItem
            key={item.id}
            rowIndex={index}
            itemId={item.id}
            name={multiple ? item[displayKey] : name}
            label={item[displayKey]}
            isSelected={value.some(i => i.id === item.id)}
            onSelect={() => selectItem(item)}
            onDeselect={() => deselectItem(item)}
            isRadio={!multiple}
          />
        )}
        renderToolbar={props => <DataListToolbar {...props} fillWidth />}
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
OptionsList.propTypes = {
  deselectItem: func.isRequired,
  displayKey: string,
  multiple: bool,
  optionCount: number.isRequired,
  options: arrayOf(Item).isRequired,
  qsConfig: QSConfig.isRequired,
  renderItemChip: func,
  searchColumns: SearchColumns,
  selectItem: func.isRequired,
  sortColumns: SortColumns,
  value: arrayOf(Item).isRequired,
};
OptionsList.defaultProps = {
  multiple: false,
  renderItemChip: null,
  searchColumns: [],
  sortColumns: [],
  displayKey: 'name',
};

export default OptionsList;
