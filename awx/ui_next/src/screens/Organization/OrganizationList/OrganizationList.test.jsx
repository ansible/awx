import React from 'react';
import { act } from 'react-dom/test-utils';

import { OrganizationsAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import OrganizationsList from './OrganizationList';

jest.mock('../../../api');

const mockOrganizations = {
  data: {
    count: 3,
    results: [
      {
        name: 'Organization 0',
        id: 1,
        url: '/organizations/1',
        summary_fields: {
          related_field_counts: {
            teams: 3,
            users: 4,
          },
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
      {
        name: 'Organization 1',
        id: 2,
        url: '/organizations/2',
        summary_fields: {
          related_field_counts: {
            teams: 2,
            users: 5,
          },
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
      {
        name: 'Organization 2',
        id: 3,
        url: '/organizations/3',
        summary_fields: {
          related_field_counts: {
            teams: 5,
            users: 6,
          },
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
    ],
  },
  isModalOpen: false,
  warningTitle: 'title',
  warningMsg: 'message',
};

describe('<OrganizationsList />', () => {
  let wrapper;
  beforeEach(() => {
    OrganizationsAPI.read.mockResolvedValue(mockOrganizations);
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

  test('Initially renders succesfully', async () => {
    await act(async () => {
      mountWithContexts(<OrganizationsList />);
    });
  });

  test('Items are rendered after loading', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    expect(wrapper.find('OrganizationListItem').length).toBe(3);
  });

  test('Item appears selected after selecting it', async () => {
    const itemCheckboxInput = 'input#select-organization-1';
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    await act(async () => {
      wrapper
        .find(itemCheckboxInput)
        .closest('DataListCheck')
        .props()
        .onChange();
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find(itemCheckboxInput).props().checked === true
    );
  });

  test('All items appear selected after select-all and unselected after unselect-all', async () => {
    const itemCheckboxInputs = [
      'input#select-organization-1',
      'input#select-organization-2',
      'input#select-organization-3',
    ];
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    // Check for initially unselected items
    await waitForElement(
      wrapper,
      'input#select-all',
      el => el.props().checked === false
    );
    itemCheckboxInputs.forEach(inputSelector => {
      const checkboxInput = wrapper
        .find('OrganizationsList')
        .find(inputSelector);
      expect(checkboxInput.props().checked === false);
    });
    // Check select-all behavior
    await act(async () => {
      wrapper
        .find('Checkbox#select-all')
        .props()
        .onChange(true);
    });
    await waitForElement(
      wrapper,
      'input#select-all',
      el => el.props().checked === true
    );
    itemCheckboxInputs.forEach(inputSelector => {
      const checkboxInput = wrapper
        .find('OrganizationsList')
        .find(inputSelector);
      expect(checkboxInput.props().checked === true);
    });
    // Check unselect-all behavior
    await act(async () => {
      wrapper
        .find('Checkbox#select-all')
        .props()
        .onChange(false);
    });
    await waitForElement(
      wrapper,
      'input#select-all',
      el => el.props().checked === false
    );
    itemCheckboxInputs.forEach(inputSelector => {
      const checkboxInput = wrapper
        .find('OrganizationsList')
        .find(inputSelector);
      expect(checkboxInput.props().checked === false);
    });
  });

  test('Expected api calls are made for multi-delete', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    expect(OrganizationsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('Checkbox#select-all')
        .props()
        .onChange(true);
    });
    await waitForElement(
      wrapper,
      'input#select-all',
      el => el.props().checked === true
    );
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

  test('Error dialog shown for failed deletion', async () => {
    const itemCheckboxInput = 'input#select-organization-1';
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
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    await act(async () => {
      wrapper
        .find(itemCheckboxInput)
        .closest('DataListCheck')
        .props()
        .onChange();
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find(itemCheckboxInput).props().checked === true
    );
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
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );
  });

  test('Add button shown for users with ability to POST', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('Add button hidden for users without ability to POST', async () => {
    OrganizationsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationsList />);
    });
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.find('ContentLoading').length === 0
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
