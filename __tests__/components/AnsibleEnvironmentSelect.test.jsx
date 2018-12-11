import React from 'react';
import { mount } from 'enzyme';
import AnsibleEnvironmentSelect from '../../src/components/AnsibleEnvironmentSelect';

describe('<AnsibleEnvironmentSelect />', () => {
  test('initially renders succesfully', async() => {
    const wrapper = mount(<AnsibleEnvironmentSelect selected="foo" selectChange={() => {}} />);
    wrapper.setState({ isHidden: false });
  });
  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(AnsibleEnvironmentSelect.prototype, 'onSelectChange');
    const wrapper = mount(<AnsibleEnvironmentSelect selected="foo" selectChange={() => {}} />);
    wrapper.setState({ isHidden: false });
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });
});