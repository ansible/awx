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
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import SelectedList from '../../SelectedList';
import PaginatedDataList from '../../PaginatedDataList';
import CheckboxListItem from '../../CheckboxListItem';
import DataListToolbar from '../../DataListToolbar';
import { QSConfig } from '@types';

function SelectList({
  value,
  options,
  optionCount,
  columns,
  multiple,
  header,
  name,
  qsConfig,
  readOnly,
  selectItem,
  deselectItem,
  renderItemChip,
  i18n,
}) {
  return (
    <div>
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
        items={options}
        itemCount={optionCount}
        pluralizedItemName={header}
        qsConfig={qsConfig}
        toolbarColumns={columns}
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
    </div>
  );
}

const Item = shape({
  id: oneOfType([number, string]).isRequired,
});
SelectList.propTypes = {
  value: arrayOf(Item).isRequired,
  options: arrayOf(Item).isRequired,
  optionCount: number.isRequired,
  columns: arrayOf(shape({})).isRequired,
  multiple: bool,
  qsConfig: QSConfig.isRequired,
  selectItem: func.isRequired,
  deselectItem: func.isRequired,
  renderItemChip: func,
};
SelectList.defaultProps = {
  multiple: false,
  renderItemChip: null,
};

export default withI18n()(SelectList);
