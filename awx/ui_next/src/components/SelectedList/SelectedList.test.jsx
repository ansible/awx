import React from 'react';
import { mount } from 'enzyme';
import { ChipGroup } from '../Chip';
import SelectedList from './SelectedList';

describe('<SelectedList />', () => {
  test('initially renders succesfully', () => {
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
    mount(
      <SelectedList
        label="Selectedeeee"
        selected={mockSelected}
        showOverflowAfter={5}
        onRemove={() => {}}
      />
    );
  });

  test('showOverflow should set showOverflow on ChipGroup', () => {
    const wrapper = mount(
      <SelectedList
        label="Selected"
        selected={[]}
        showOverflowAfter={5}
        onRemove={() => {}}
      />
    );
    const chipGroup = wrapper.find(ChipGroup);
    expect(chipGroup).toHaveLength(1);
    expect(chipGroup.prop('showOverflowAfter')).toEqual(5);
  });

  test('Clicking remove on chip calls onRemove callback prop with correct params', () => {
    const onRemove = jest.fn();
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
    ];
    const wrapper = mount(
      <SelectedList
        label="Selected"
        selected={mockSelected}
        showOverflowAfter={3}
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
