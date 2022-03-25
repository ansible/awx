import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  DataList,
  DataListAction,
  DataListItem,
  DataListCell,
  DataListItemRow,
  DataListControl,
  DataListDragButton,
  DataListItemCells,
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
  const [liveText, setLiveText] = useState('');
  const [id, setId] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const onDragStart = (newId) => {
    setId(newId);
    setLiveText(t`Dragging started for item id: ${newId}.`);
    setIsDragging(true);
  };

  const onDragMove = (oldIndex, newIndex) => {
    setLiveText(
      t`Dragging item ${id}. Item with index ${oldIndex} in now ${newIndex}.`
    );
  };

  const onDragCancel = () => {
    setLiveText(t`Dragging cancelled. List is unchanged.`);
    setIsDragging(false);
  };

  const onDragFinish = (newItemOrder) => {
    const selectedItems = newItemOrder.map((item) =>
      selected.find((i) => i.name === item)
    );
    onRowDrag(selectedItems);
    setIsDragging(false);
  };

  const removeItem = (item) => {
    onRemove(selected.find((i) => i.name === item));
  };

  if (selected.length <= 0) {
    return null;
  }

  const orderedList = selected.map((item) => item?.name);

  return (
    <>
      <DataList
        aria-label={t`Draggable list to reorder and remove selected items.`}
        data-cy="draggable-list"
        itemOrder={orderedList}
        onDragCancel={onDragCancel}
        onDragFinish={onDragFinish}
        onDragMove={onDragMove}
        onDragStart={onDragStart}
      >
        {orderedList.map((label, index) => {
          const rowPosition = index + 1;
          return (
            <DataListItem id={label} key={rowPosition}>
              <DataListItemRow>
                <DataListControl>
                  <DataListDragButton
                    aria-label={t`Reorder`}
                    aria-labelledby={rowPosition}
                    aria-describedby={t`Press space or enter to begin dragging,
                    and use the arrow keys to navigate up or down.
                    Press enter to confirm the drag, or any other key to
                    cancel the drag operation.`}
                    aria-pressed="false"
                    data-cy={`reorder-${label}`}
                    isDisabled={selected.length === 1}
                  />
                </DataListControl>
                <DataListItemCells
                  dataListCells={[
                    <DataListCell key={label}>
                      <span id={rowPosition}>{`${rowPosition}. ${label}`}</span>
                    </DataListCell>,
                  ]}
                />
                <RemoveActionSection aria-label={t`Actions`} id={rowPosition}>
                  <Button
                    onClick={() => removeItem(label)}
                    variant="plain"
                    aria-label={t`Remove`}
                    ouiaId={`draggable-list-remove-${label}`}
                    isDisabled={isDragging}
                  >
                    <TimesIcon />
                  </Button>
                </RemoveActionSection>
              </DataListItemRow>
            </DataListItem>
          );
        })}
      </DataList>
      <div className="pf-screen-reader" aria-live="assertive">
        {liveText}
      </div>
    </>
  );
}

const ListItem = PropTypes.shape({
  id: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
});
DraggableSelectedList.propTypes = {
  onRemove: PropTypes.func,
  onRowDrag: PropTypes.func,
  selected: PropTypes.arrayOf(ListItem),
};
DraggableSelectedList.defaultProps = {
  onRemove: () => null,
  onRowDrag: () => null,
  selected: [],
};

export default DraggableSelectedList;
