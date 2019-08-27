import React from 'react';
import { sleep } from '@testUtils/testUtils';
import MultiSelect, { _MultiSelect } from './MultiSelect';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

describe('<MultiSelect />', () => {
  const associatedItems = [
    { name: 'Foo', id: 1, organization: 1 },
    { name: 'Bar', id: 2, organization: 1 },
  ];
  const options = [{ name: 'Angry', id: 3 }, { name: 'Potato', id: 4 }];

  test('Initially render successfully', () => {
    const getInitialChipItems = jest.spyOn(
      _MultiSelect.prototype,
      'getInitialChipItems'
    );
    const wrapper = mountWithContexts(
      <MultiSelect
        onAddNewItem={jest.fn()}
        onRemoveItem={jest.fn()}
        associatedItems={associatedItems}
        options={options}
      />
    );
    const component = wrapper.find('MultiSelect');

    expect(getInitialChipItems).toBeCalled();
    expect(component.state().chipItems.length).toBe(2);
  });

  test('handleSelection add item to chipItems', async () => {
    const wrapper = mountWithContexts(
      <MultiSelect
        onAddNewItem={jest.fn()}
        onRemoveItem={jest.fn()}
        associatedItems={associatedItems}
        options={options}
      />
    );
    const component = wrapper.find('MultiSelect');
    component
      .find('input[aria-label="labels"]')
      .simulate('keydown', { key: 'Enter' });
    component.update();
    await sleep(1);
    expect(component.state().chipItems.length).toBe(2);
  });

  test('handleAddItem adds a chip only when Tab is pressed', () => {
    const onAddNewItem = jest.fn();
    const onChange = jest.fn();
    const wrapper = mountWithContexts(
      <MultiSelect
        onAddNewItem={onAddNewItem}
        onRemoveItem={jest.fn()}
        onChange={onChange}
        associatedItems={associatedItems}
        options={options}
      />
    );
    const event = {
      preventDefault: () => {},
      key: 'Enter',
    };
    const component = wrapper.find('MultiSelect');

    component.setState({ input: 'newLabel' });
    component.update();
    component.instance().handleAddItem(event);
    expect(component.state().chipItems.length).toBe(3);
    expect(component.state().input.length).toBe(0);
    expect(component.state().isExpanded).toBe(false);
    expect(onAddNewItem).toBeCalled();
    expect(onChange).toBeCalled();
  });

  test('removeChip removes chip properly', () => {
    const onRemoveItem = jest.fn();
    const onChange = jest.fn();

    const wrapper = mountWithContexts(
      <MultiSelect
        onAddNewItem={jest.fn()}
        onRemoveItem={onRemoveItem}
        onChange={onChange}
        associatedItems={associatedItems}
        options={options}
      />
    );
    const event = {
      preventDefault: () => {},
    };
    const component = wrapper.find('MultiSelect');
    component
      .instance()
      .removeChip(event, { name: 'Foo', id: 1, organization: 1 });
    expect(component.state().chipItems.length).toBe(1);
    expect(onRemoveItem).toBeCalled();
    expect(onChange).toBeCalled();
  });
});
