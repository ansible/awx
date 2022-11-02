import React from 'react';
import { act } from 'react-dom/test-utils';
import { WorkflowApprovalsAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PageHeaderToolbar from './PageHeaderToolbar';

jest.mock('../../api');

let wrapper;

describe('PageHeaderToolbar', () => {
  const pageHelpDropdownSelector = 'Dropdown QuestionCircleIcon';
  const pageUserDropdownSelector = 'Dropdown UserIcon';
  const onAboutClick = jest.fn();
  const onLogoutClick = jest.fn();

  test('expected content is rendered on initialization', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <PageHeaderToolbar
          onAboutClick={onAboutClick}
          onLogoutClick={onLogoutClick}
        />
      );
    });

    expect(
      wrapper.find(
        'Link[to="/workflow_approvals?workflow_approvals.status=pending"]'
      )
    ).toHaveLength(1);
    expect(wrapper.find(pageHelpDropdownSelector)).toHaveLength(1);
    expect(wrapper.find(pageUserDropdownSelector)).toHaveLength(1);
  });

  test('dropdowns have expected items and callbacks', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <PageHeaderToolbar
          onAboutClick={onAboutClick}
          onLogoutClick={onLogoutClick}
          loggedInUser={{ id: 1 }}
        />
      );
    });
    expect(wrapper.find('DropdownItem')).toHaveLength(0);
    wrapper.find(pageHelpDropdownSelector).simulate('click');
    expect(wrapper.find('DropdownItem')).toHaveLength(2);

    const about = wrapper.find('DropdownItem li button');
    about.simulate('click');
    expect(onAboutClick).toHaveBeenCalled();

    expect(wrapper.find('DropdownItem')).toHaveLength(0);
    wrapper.find(pageUserDropdownSelector).simulate('click');
    wrapper.update();
    expect(
      wrapper.find('DropdownItem[aria-label="User details"]').prop('href')
    ).toBe('#/users/1/details');
    expect(wrapper.find('DropdownItem')).toHaveLength(2);

    const logout = wrapper.find('DropdownItem li button');
    logout.simulate('click');
    expect(onLogoutClick).toHaveBeenCalled();
  });

  test('pending workflow approvals count set correctly', async () => {
    WorkflowApprovalsAPI.read.mockResolvedValueOnce({
      data: {
        count: 20,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <PageHeaderToolbar
          onAboutClick={onAboutClick}
          onLogoutClick={onLogoutClick}
        />
      );
    });

    expect(
      wrapper.find('NotificationBadge#toolbar-workflow-approval-badge').text()
    ).toEqual('20');
  });
});
