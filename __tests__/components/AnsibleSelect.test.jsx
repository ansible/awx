import React from 'react';
import { mount } from 'enzyme';
import AnsibleSelect from '../../src/components/AnsibleSelect';

const label = "test select"
const mockData = ["/venv/baz/", "/venv/ansible/"];
describe('<AnsibleSelect />', () => {
  test('initially renders succesfully', async () => {
    mount(
      <AnsibleSelect
        selected="foo"
        selectChange={() => { }}
        labelName={label}
        data={mockData}
      />
    );
  });
  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(AnsibleSelect.prototype, 'onSelectChange');
    const wrapper = mount(
      <AnsibleSelect
        selected="foo"
        selectChange={() => { }}
        labelName={label}
        data={mockData}
      />
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });
});