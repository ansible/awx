import React from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  DataListAction,
  DragDrop,
  Droppable,
  Draggable,
  DataListItemRow,
  DataListItemCells,
  DataList,
  DataListItem,
  DataListCell,
  DataListControl,
  DataListDragButton,
} from '@patternfly/react-core';
import { TimesIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { t } from '@lingui/macro';

const RemoveActionSection = styled(DataListAction)`
  && {
    align-items: center;
    padding: 0;
  }
`;

function DraggableSelectedList({ selected, onRemove, onRowDrag }) {
  const removeItem = (item) => {
    onRemove(selected.find((i) => i.name === item));
  };

  function reorder(list, startIndex, endIndex) {
    const result = Array.from(list);
    const [removed] = result.splice(startIndex, 1);
    result.splice(endIndex, 0, removed);
    return result;
  }

  function dragItem(item, dest) {
    if (!dest || item.index === dest.index) {
      return false;
    }

    const newItems = reorder(selected, item.index, dest.index);
    onRowDrag(newItems);
    return true;
  }

  if (selected.length <= 0) {
    return null;
  }

  return (
    <DragDrop onDrop={dragItem}>
      <Droppable>
        <DataList>
          {selected.map(({ name: label, id }, index) => {
            const rowPosition = index + 1;
            return (
              <Draggable value={id} key={rowPosition}>
                <DataListItem>
                  <DataListItemRow>
                    <DataListControl>
                      <DataListDragButton isDisabled={selected.length < 2} />
                    </DataListControl>
                    <DataListItemCells
                      dataListCells={[
                        <DataListCell key={label}>
                          <span
                            id={rowPosition}
                          >{`${rowPosition}. ${label}`}</span>
                        </DataListCell>,
                      ]}
                    />
                    <RemoveActionSection>
                      <Button
                        onClick={() => removeItem(label)}
                        variant="plain"
                        aria-label={t`Remove`}
                        ouiaId={`draggable-list-remove-${label}`}
                      >
                        <TimesIcon />
                      </Button>
                    </RemoveActionSection>
                  </DataListItemRow>
                </DataListItem>
              </Draggable>
            );
          })}
        </DataList>
      </Droppable>
    </DragDrop>
  );
}

const SelectedListItem = PropTypes.shape({
  id: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
});
DraggableSelectedList.propTypes = {
  onRemove: PropTypes.func,
  onRowDrag: PropTypes.func,
  selected: PropTypes.arrayOf(SelectedListItem),
};
DraggableSelectedList.defaultProps = {
  onRemove: () => null,
  onRowDrag: () => null,
  selected: [],
};

export default DraggableSelectedList;
