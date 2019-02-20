import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import AnsibleSelect from '../../src/components/AnsibleSelect';

const label = 'test select';
const mockData = ['/venv/baz/', '/venv/ansible/'];
describe('<AnsibleSelect />', () => {
  test('initially renders succesfully', async () => {
    mount(
      <I18nProvider>
        <AnsibleSelect
          value="foo"
          name="bar"
          onChange={() => { }}
          label={label}
          data={mockData}
        />
      </I18nProvider>
    );
  });

  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(AnsibleSelect.prototype, 'onSelectChange');
    const wrapper = mount(
      <I18nProvider>
        <AnsibleSelect
          value="foo"
          name="bar"
          onChange={() => { }}
          label={label}
          data={mockData}
        />
      </I18nProvider>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });

  test('Returns correct select options if defaultSelected props is passed', () => {
    const wrapper = mount(
      <I18nProvider>
        <AnsibleSelect
          value="foo"
          name="bar"
          onChange={() => { }}
          label={label}
          data={mockData}
          defaultSelected={mockData[1]}
        />
      </I18nProvider>
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
  });
});
