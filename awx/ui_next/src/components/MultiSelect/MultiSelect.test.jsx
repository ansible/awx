import React from 'react';
import { mount, shallow } from 'enzyme';
import MultiSelect from './MultiSelect';

describe('<MultiSelect />', () => {
  const value = [
    { name: 'Foo', id: 1, organization: 1 },
    { name: 'Bar', id: 2, organization: 1 },
  ];
  const options = [{ name: 'Angry', id: 3 }, { name: 'Potato', id: 4 }];

  test('should render successfully', () => {
    const wrapper = shallow(
      <MultiSelect
        onAddNewItem={jest.fn()}
        onRemoveItem={jest.fn()}
        value={value}
        options={options}
      />
    );

    expect(wrapper.find('Chip')).toHaveLength(2);
  });

  test('should add item when typed', async () => {
    const onChange = jest.fn();
    const onAdd = jest.fn();
    const wrapper = mount(
      <MultiSelect
        onAddNewItem={onAdd}
        onRemoveItem={jest.fn()}
        onChange={onChange}
        value={value}
        options={options}
      />
    );
    const component = wrapper.find('MultiSelect');
    const input = component.find('TextInput');
    input.invoke('onChange')('Flabadoo');
    input.simulate('keydown', { key: 'Enter' });

    expect(onAdd.mock.calls[0][0].name).toEqual('Flabadoo');
    const newVal = onChange.mock.calls[0][0];
    expect(newVal).toHaveLength(3);
    expect(newVal[2].name).toEqual('Flabadoo');
  });

  test('should add item when clicked from menu', () => {
    const onAddNewItem = jest.fn();
    const onChange = jest.fn();
    const wrapper = mount(
      <MultiSelect
        onAddNewItem={onAddNewItem}
        onRemoveItem={jest.fn()}
        onChange={onChange}
        value={value}
        options={options}
      />
    );

    const input = wrapper.find('TextInput');
    input.simulate('focus');
    wrapper.update();
    const event = {
      preventDefault: () => {},
      target: wrapper
        .find('DropdownItem')
        .at(1)
        .getDOMNode(),
    };
    wrapper
      .find('DropdownItem')
      .at(1)
      .invoke('onClick')(event);

    expect(onAddNewItem).toHaveBeenCalledWith(options[1]);
    const newVal = onChange.mock.calls[0][0];
    expect(newVal).toHaveLength(3);
    expect(newVal[2]).toEqual(options[1]);
  });

  test('should remove item', () => {
    const onRemoveItem = jest.fn();
    const onChange = jest.fn();
    const wrapper = mount(
      <MultiSelect
        onAddNewItem={jest.fn()}
        onRemoveItem={onRemoveItem}
        onChange={onChange}
        value={value}
        options={options}
      />
    );

    const chips = wrapper.find('PFChip');
    expect(chips).toHaveLength(2);
    chips.at(1).invoke('onClick')();

    expect(onRemoveItem).toHaveBeenCalledWith(value[1]);
    const newVal = onChange.mock.calls[0][0];
    expect(newVal).toHaveLength(1);
    expect(newVal).toEqual([value[0]]);
  });
});
