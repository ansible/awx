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
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import SelectedList from '../../SelectedList';
import PaginatedDataList from '../../PaginatedDataList';
import CheckboxListItem from '../../CheckboxListItem';
import DataListToolbar from '../../DataListToolbar';
import { QSConfig, SearchColumns, SortColumns } from '@types';

const ModalList = styled.div`
  .pf-c-data-toolbar__content {
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
  multiple,
  header,
  name,
  qsConfig,
  readOnly,
  selectItem,
  deselectItem,
  renderItemChip,
  isLoading,
  i18n,
}) {
  return (
    <ModalList>
      {value.length > 0 && (
        <SelectedList
          label={i18n._(t`Selected`)}
          selected={value}
          showOverflowAfter={5}
          onRemove={item => deselectItem(item)}
          isReadOnly={readOnly}
          renderItemChip={renderItemChip}
        />
      )}
      <PaginatedDataList
        contentError={contentError}
        items={options}
        itemCount={optionCount}
        pluralizedItemName={header}
        qsConfig={qsConfig}
        toolbarSearchColumns={searchColumns}
        toolbarSortColumns={sortColumns}
        hasContentLoading={isLoading}
        onRowClick={selectItem}
        renderItem={item => (
          <CheckboxListItem
            key={item.id}
            itemId={item.id}
            name={multiple ? item.name : name}
            label={item.name}
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
  value: arrayOf(Item).isRequired,
  options: arrayOf(Item).isRequired,
  optionCount: number.isRequired,
  searchColumns: SearchColumns,
  sortColumns: SortColumns,
  multiple: bool,
  qsConfig: QSConfig.isRequired,
  selectItem: func.isRequired,
  deselectItem: func.isRequired,
  renderItemChip: func,
};
OptionsList.defaultProps = {
  multiple: false,
  renderItemChip: null,
  searchColumns: [],
  sortColumns: [],
};

export default withI18n()(OptionsList);
