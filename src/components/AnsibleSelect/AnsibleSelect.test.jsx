import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import AnsibleSelect, { _AnsibleSelect } from './AnsibleSelect';

const label = 'test select';
const mockData = ['/venv/baz/', '/venv/ansible/'];
describe('<AnsibleSelect />', () => {
  test('initially renders succesfully', async () => {
    mountWithContexts(
      <AnsibleSelect
        value="foo"
        name="bar"
        onChange={() => { }}
        label={label}
        data={mockData}
      />
    );
  });

  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(_AnsibleSelect.prototype, 'onSelectChange');
    const wrapper = mountWithContexts(
      <AnsibleSelect
        value="foo"
        name="bar"
        onChange={() => { }}
        label={label}
        data={mockData}
      />
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });

  test('Returns correct select options if defaultSelected props is passed', () => {
    const wrapper = mountWithContexts(
      <AnsibleSelect
        value="foo"
        name="bar"
        onChange={() => { }}
        label={label}
        data={mockData}
        defaultSelected={mockData[1]}
      />
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
  });
});
