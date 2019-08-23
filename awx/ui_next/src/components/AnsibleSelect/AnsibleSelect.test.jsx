import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import AnsibleSelect, { _AnsibleSelect } from './AnsibleSelect';

const mockData = [
  {
    key: 'baz',
    label: 'Baz',
    value: '/venv/baz/',
  },
  {
    key: 'default',
    label: 'Default',
    value: '/venv/ansible/',
  },
];

describe('<AnsibleSelect />', () => {
  test('initially renders succesfully', async () => {
    mountWithContexts(
      <AnsibleSelect
        id="bar"
        value="foo"
        name="bar"
        onChange={() => {}}
        data={mockData}
      />
    );
  });

  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(_AnsibleSelect.prototype, 'onSelectChange');
    const wrapper = mountWithContexts(
      <AnsibleSelect
        id="bar"
        value="foo"
        name="bar"
        onChange={() => {}}
        data={mockData}
      />
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });

  test('Returns correct select options', () => {
    const wrapper = mountWithContexts(
      <AnsibleSelect
        id="bar"
        value="foo"
        name="bar"
        onChange={() => {}}
        data={mockData}
      />
    );

    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });
});
