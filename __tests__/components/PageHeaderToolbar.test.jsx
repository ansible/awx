import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import { I18nProvider } from '@lingui/react';
import PageHeaderToolbar from '../../src/components/PageHeaderToolbar';

describe('PageHeaderToolbar', () => {
  const pageHelpDropdownSelector = 'Dropdown QuestionCircleIcon';
  const pageUserDropdownSelector = 'Dropdown UserIcon';
  const onAboutClick = jest.fn();
  const onLogoutClick = jest.fn();

  test('expected content is rendered on initialization', () => {
    const wrapper = mount(
      <I18nProvider>
        <PageHeaderToolbar
          onAboutClick={onAboutClick}
          onLogoutClick={onLogoutClick}
        />
      </I18nProvider>
    );

    expect(wrapper.find(pageHelpDropdownSelector)).toHaveLength(1);
    expect(wrapper.find(pageUserDropdownSelector)).toHaveLength(1);
  });

  test('dropdowns have expected items and callbacks', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <PageHeaderToolbar
            onAboutClick={onAboutClick}
            onLogoutClick={onLogoutClick}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(wrapper.find('DropdownItem')).toHaveLength(0);
    wrapper.find(pageHelpDropdownSelector).simulate('click');
    expect(wrapper.find('DropdownItem')).toHaveLength(2);

    const about = wrapper.find('DropdownItem li button');
    about.simulate('click');
    expect(onAboutClick).toHaveBeenCalled();

    expect(wrapper.find('DropdownItem')).toHaveLength(0);
    wrapper.find(pageUserDropdownSelector).simulate('click');
    expect(wrapper.find('DropdownItem')).toHaveLength(2);

    const logout = wrapper.find('DropdownItem li button');
    logout.simulate('click');
    expect(onLogoutClick).toHaveBeenCalled();
  });
});
