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
import SelectedList from '../SelectedList';
import PaginatedDataList from '../PaginatedDataList';
import CheckboxListItem from '../CheckboxListItem';
import DataListToolbar from '../DataListToolbar';
import { QSConfig, SearchColumns, SortColumns } from '../../types';

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
  i18n,
  displayKey,
}) {
  return (
    <ModalList>
      {value.length > 0 && (
        <SelectedList
          label={i18n._(t`Selected`)}
          selected={value}
          onRemove={item => deselectItem(item)}
          isReadOnly={readOnly}
          renderItemChip={renderItemChip}
          displayKey={displayKey}
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
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        hasContentLoading={isLoading}
        onRowClick={selectItem}
        renderItem={item => (
          <CheckboxListItem
            key={item.id}
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

export default withI18n()(OptionsList);
