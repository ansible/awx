import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ChipGroup from '../ChipGroup';

import SelectedList from './SelectedList';

describe('<SelectedList />', () => {
  test('initially renders successfully', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
      {
        id: 2,
        name: 'bar',
      },
    ];
    const wrapper = mountWithContexts(
      <SelectedList
        label="Selectedeeee"
        selected={mockSelected}
        onRemove={() => {}}
      />
    );
    expect(wrapper.length).toBe(1);
  });

  test('showOverflow should set showOverflow on ChipGroup', () => {
    const wrapper = mountWithContexts(
      <SelectedList label="Selected" selected={[]} onRemove={() => {}} />
    );
    const chipGroup = wrapper.find(ChipGroup);
    expect(chipGroup).toHaveLength(1);
    expect(chipGroup.prop('numChips')).toEqual(5);
  });

  test('Clicking remove on chip calls onRemove callback prop with correct params', () => {
    const onRemove = jest.fn();
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
    ];
    const wrapper = mountWithContexts(
      <SelectedList
        label="Selected"
        selected={mockSelected}
        onRemove={onRemove}
      />
    );
    wrapper
      .find('.pf-c-chip button')
      .first()
      .simulate('click');
    expect(onRemove).toBeCalledWith({
      id: 1,
      name: 'foo',
    });
  });
});
