import React from 'react';
import { mount } from 'enzyme';
import AnsibleSelect from '../../src/components/AnsibleSelect';

const mockData = ['foo', 'bar'];
describe('<AnsibleSelect />', () => {
  test('initially renders succesfully', async() => {
    const wrapper = mount(<AnsibleSelect selected="foo" data={mockData} selectChange={() => {}} />);
    wrapper.setState({ isHidden: false });
  });
  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(AnsibleSelect.prototype, 'onSelectChange');
    const wrapper = mount(<AnsibleSelect selected="foo" data={mockData} selectChange={() => {}} />);
    wrapper.setState({ isHidden: false });
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });
});