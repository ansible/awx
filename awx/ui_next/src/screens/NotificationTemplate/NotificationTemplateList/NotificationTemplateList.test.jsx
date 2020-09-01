import React from 'react';
import { act } from 'react-dom/test-utils';
import { OrganizationsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import NotificationTemplateList from './NotificationTemplateList';

jest.mock('../../../api');

const mockTemplates = {
  data: {
    count: 3,
    results: [
      {
        name: 'Boston',
        id: 1,
        url: '/notification_templates/1',
        type: 'slack',
        summary_fields: {
          recent_notifications: [
            {
              status: 'success',
            },
          ],
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
      {
        name: 'Minneapolis',
        id: 2,
        url: '/notification_templates/2',
        summary_fields: {
          recent_notifications: [],
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
      {
        name: 'Philidelphia',
        id: 3,
        url: '/notification_templates/3',
        summary_fields: {
          recent_notifications: [
            {
              status: 'failed',
            },
            {
              status: 'success',
            },
          ],
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
    ],
  },
};

describe('<NotificationTemplateList />', () => {
  let wrapper;
  beforeEach(() => {
    OrganizationsAPI.read.mockResolvedValue(mockTemplates);
    OrganizationsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should load notifications', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<NotificationTemplateList />);
    });
    wrapper.update();
    expect(OrganizationsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('NotificationTemplateListItem').length).toBe(3);
  });

  test('should select item', async () => {
    const itemCheckboxInput = 'input#select-template-1';
    await act(async () => {
      wrapper = mountWithContexts(<NotificationTemplateList />);
    });
    wrapper.update();
    expect(wrapper.find(itemCheckboxInput).prop('checked')).toEqual(false);
    await act(async () => {
      wrapper
        .find(itemCheckboxInput)
        .closest('DataListCheck')
        .props()
        .onChange();
    });
    wrapper.update();
    expect(wrapper.find(itemCheckboxInput).prop('checked')).toEqual(true);
  });

  test('should delete notifications', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<NotificationTemplateList />);
    });
    wrapper.update();
    expect(OrganizationsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('Checkbox#select-all')
        .props()
        .onChange(true);
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Delete"]').simulate('click');
      wrapper.update();
    });
    const deleteButton = global.document.querySelector(
      'body div[role="dialog"] button[aria-label="confirm delete"]'
    );
    expect(deleteButton).not.toEqual(null);
    await act(async () => {
      deleteButton.click();
    });
    expect(OrganizationsAPI.destroy).toHaveBeenCalledTimes(3);
    expect(OrganizationsAPI.read).toHaveBeenCalledTimes(2);
  });

  test('should show error dialog shown for failed deletion', async () => {
    const itemCheckboxInput = 'input#select-template-1';
    OrganizationsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/organizations/1',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<NotificationTemplateList />);
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find(itemCheckboxInput)
        .closest('DataListCheck')
        .props()
        .onChange();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Delete"]').simulate('click');
      wrapper.update();
    });
    const deleteButton = global.document.querySelector(
      'body div[role="dialog"] button[aria-label="confirm delete"]'
    );
    expect(deleteButton).not.toEqual(null);
    await act(async () => {
      deleteButton.click();
    });
    wrapper.update();

    const modal = wrapper.find('Modal');
    expect(modal.prop('isOpen')).toEqual(true);
    expect(modal.prop('title')).toEqual('Error!');
  });

  test('should show add button', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<NotificationTemplateList />);
    });
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('should hide add button (rbac)', async () => {
    OrganizationsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<NotificationTemplateList />);
    });
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
