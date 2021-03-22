import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import AnsibleSelect from './AnsibleSelect';

const mockData = [
  {
    key: 'baz',
    label: 'Baz',
    value: '/var/lib/awx/venv/baz/',
  },
  {
    key: 'default',
    label: 'Default',
    value: '/var/lib/awx/venv/ansible/',
  },
];

describe('<AnsibleSelect />', () => {
  const onChange = jest.fn();
  test('initially renders successfully', async () => {
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
    const wrapper = mountWithContexts(
      <AnsibleSelect
        id="bar"
        value="foo"
        name="bar"
        onChange={onChange}
        data={mockData}
      />
    );
    expect(onChange).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(onChange).toHaveBeenCalled();
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
