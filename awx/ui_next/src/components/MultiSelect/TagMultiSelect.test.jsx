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

  it('should trigger onChange', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={onChange} />
    );

    const select = wrapper.find('MultiSelect');
    select.invoke('onChange')([
      { name: 'foo' },
      { name: 'bar' },
      { name: 'baz' },
    ]);
    expect(onChange).toHaveBeenCalledWith('foo,bar,baz');
  });
});
