import React from 'react';
import { mount } from 'enzyme';
import TagMultiSelect from './TagMultiSelect';

describe('<TagMultiSelect />', () => {
  it('should render MultiSelect', () => {
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={jest.fn()} />
    );
    expect(wrapper.find('MultiSelect').prop('options')).toEqual([
      { id: 'foo', name: 'foo' },
      { id: 'bar', name: 'bar' },
    ]);
  });

  it('should not treat empty string as an option', () => {
    const wrapper = mount(<TagMultiSelect value="" onChange={jest.fn()} />);
    expect(wrapper.find('MultiSelect').prop('options')).toEqual([]);
  });

  // NOTE: this test throws a warning which *should* be go away once we upgrade
  // to React 16.8 (https://github.com/airbnb/enzyme/blob/master/docs/api/ReactWrapper/invoke.md)
  it('should trigger onChange', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={onChange} />
    );

    const input = wrapper.find('TextInput');
    input.invoke('onChange')('baz');
    input.invoke('onKeyDown')({ key: 'Tab' });
    expect(onChange).toHaveBeenCalledWith('foo,bar,baz');
  });
});
