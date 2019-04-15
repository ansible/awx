import React from 'react';
import { mount } from 'enzyme';

import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import Organization, { _Organization } from '../../../../../src/pages/Organizations/screens/Organization/Organization';

describe('<OrganizationView />', () => {
  test('initially renders succesfully', () => {
    const spy = jest.spyOn(_Organization.prototype, 'checkLocation');
    mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <_Organization
            match={{ path: '/organizations/:id', url: '/organizations/1' }}
            location={{ search: '', pathname: '/organizations/1' }}
          />
        </MemoryRouter>
      </I18nProvider>
    );
    expect(spy).toHaveBeenCalled();
  });

  test('handleTabSelect renders the correct tab', async () => {
    const currentTab = 'organizations/19/access';
    const spy = jest.spyOn(_Organization.prototype, 'handleTabSelect');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <Organization location={currentTab} />
        </MemoryRouter>
      </I18nProvider>
    ).find('Organization');
    wrapper.find('button').at(2).simulate('click');
    setImmediate(async () => {
      wrapper.setState({ activeTabKey: 1 });
    });
    wrapper.update();
    expect(spy).toBeCalled();
    expect(wrapper.state('activeTabKey')).toBe(1);
  });

  test('checkLocation renders proper state when new tab is selected', async () => {
    const currentTab = 'organizations/19/access';
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <Organization location={currentTab} />
        </MemoryRouter>
      </I18nProvider>
    ).find('Organization');
    setImmediate(async () => {
      wrapper.setState({ activeTabKey: 1 });
    });
    wrapper.find('button').at(3).simulate('click');
    expect(wrapper.state('activeTabKey')).toBe(2);
  });
});
