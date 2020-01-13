import React from 'react';
import { mount } from 'enzyme';
import TagMultiSelect from './TagMultiSelect';

describe('<TagMultiSelect />', () => {
  it('should render Select', () => {
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={jest.fn()} />
    );
    wrapper.find('input').simulate('focus');
    const options = wrapper.find('SelectOption');
    expect(options).toHaveLength(2);
    expect(options.at(0).prop('value')).toEqual('foo');
    expect(options.at(1).prop('value')).toEqual('bar');
  });

  it('should not treat empty string as an option', () => {
    const wrapper = mount(<TagMultiSelect value="" onChange={jest.fn()} />);
    wrapper.find('input').simulate('focus');
    expect(wrapper.find('Select').prop('isExpanded')).toEqual(true);
    expect(wrapper.find('SelectOption')).toHaveLength(0);
  });

  it('should trigger onChange', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={onChange} />
    );
    wrapper.find('input').simulate('focus');

    wrapper.find('Select').invoke('onSelect')(null, 'baz');
    expect(onChange).toHaveBeenCalledWith('foo,bar,baz');
  });
});
