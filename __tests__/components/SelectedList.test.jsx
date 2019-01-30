import React from 'react';
import { mount } from 'enzyme';
import SelectedList from '../../src/components/SelectedList';

describe('<SelectedList />', () => {
  test('initially renders succesfully', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo'
      }, {
        id: 2,
        name: 'bar'
      }
    ];
    mount(
      <SelectedList
        label="Selected"
        selected={mockSelected}
        showOverflowAfter={5}
        onRemove={() => {}}
      />
    );
  });
  test('showOverflow should set showOverflow state to true', () => {
    const wrapper = mount(
      <SelectedList
        label="Selected"
        selected={[]}
        showOverflowAfter={5}
        onRemove={() => {}}
      />
    );
    expect(wrapper.state('showOverflow')).toBe(false);
    wrapper.instance().showOverflow();
    expect(wrapper.state('showOverflow')).toBe(true);
  });
  test('Overflow chip should be shown when more selected.length exceeds showOverflowAfter', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo'
      }, {
        id: 2,
        name: 'bar'
      }, {
        id: 3,
        name: 'foobar'
      }, {
        id: 4,
        name: 'baz'
      }, {
        id: 5,
        name: 'foobaz'
      }
    ];
    const wrapper = mount(
      <SelectedList
        label="Selected"
        selected={mockSelected}
        showOverflowAfter={3}
        onRemove={() => {}}
      />
    );
    expect(wrapper.find('Chip').length).toBe(4);
    expect(wrapper.find('[isOverflowChip=true]').length).toBe(1);
  });
  test('Clicking overflow chip should show all chips', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo'
      }, {
        id: 2,
        name: 'bar'
      }, {
        id: 3,
        name: 'foobar'
      }, {
        id: 4,
        name: 'baz'
      }, {
        id: 5,
        name: 'foobaz'
      }
    ];
    const wrapper = mount(
      <SelectedList
        label="Selected"
        selected={mockSelected}
        showOverflowAfter={3}
        onRemove={() => {}}
      />
    );
    expect(wrapper.find('Chip').length).toBe(4);
    expect(wrapper.find('[isOverflowChip=true]').length).toBe(1);
    wrapper.find('[isOverflowChip=true] button').simulate('click');
    expect(wrapper.find('Chip').length).toBe(5);
    expect(wrapper.find('[isOverflowChip=true]').length).toBe(0);
  });
  test('Clicking remove on chip calls onRemove callback prop with correct params', () => {
    const onRemove = jest.fn();
    const mockSelected = [
      {
        id: 1,
        name: 'foo'
      }
    ];
    const wrapper = mount(
      <SelectedList
        label="Selected"
        selected={mockSelected}
        showOverflowAfter={3}
        onRemove={onRemove}
      />
    );
    wrapper.find('.pf-c-chip button').first().simulate('click');
    expect(onRemove).toBeCalledWith({
      id: 1,
      name: 'foo'
    });
  });
});
