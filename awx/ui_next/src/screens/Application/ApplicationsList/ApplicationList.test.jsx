import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { ApplicationsAPI } from '../../../api';
import ApplicationsList from './ApplicationsList';

jest.mock('../../../api/models/Applications');

const applications = {
  data: {
    results: [
      {
        id: 1,
        name: 'Foo',
        summary_fields: {
          organization: { name: 'Org 1', id: 10 },
          user_capabilities: { edit: true, delete: true },
        },
        url: '',
        organization: 10,
      },
      {
        id: 2,
        name: 'Bar',
        summary_fields: {
          organization: { name: 'Org 2', id: 20 },
          user_capabilities: { edit: true, delete: true },
        },
        url: '',
        organization: 20,
      },
    ],
    count: 2,
  },
};
const options = { data: { actions: { POST: true } } };
describe('<ApplicationsList/>', () => {
  let wrapper;
  test('should mount properly', async () => {
    ApplicationsAPI.read.mockResolvedValue(applications);
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });
    await waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);
  });

  test('should have data fetched and render 2 rows', async () => {
    ApplicationsAPI.read.mockResolvedValue(applications);
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });
    await waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);
    expect(wrapper.find('ApplicationListItem').length).toBe(2);
    expect(ApplicationsAPI.read).toBeCalled();
    expect(ApplicationsAPI.readOptions).toBeCalled();
  });

  test('should delete item successfully', async () => {
    ApplicationsAPI.read.mockResolvedValue(applications);
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });
    waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);

    wrapper
      .find('.pf-c-table__check')
      .first()
      .find('input')
      .simulate('change', applications.data.results[0]);

    wrapper.update();

    expect(
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .prop('checked')
    ).toBe(true);
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );

    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    expect(ApplicationsAPI.destroy).toBeCalledWith(
      applications.data.results[0].id
    );
  });

  test('should throw content error', async () => {
    ApplicationsAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/applications/',
          },
          data: 'An error occurred',
        },
      })
    );
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });

    await waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should render deletion error modal', async () => {
    ApplicationsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/applications/',
          },
          data: 'An error occurred',
        },
      })
    );
    ApplicationsAPI.read.mockResolvedValue(applications);
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });
    waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);

    wrapper
      .find('.pf-c-table__check')
      .first()
      .find('input')
      .simulate('change', 'a');

    wrapper.update();

    expect(
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .prop('checked')
    ).toBe(true);
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );

    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();

    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });

  test('should not render add button', async () => {
    ApplicationsAPI.read.mockResolvedValue(applications);
    ApplicationsAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });
    waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });

  test('should not render edit button for first list item', async () => {
    applications.data.results[0].summary_fields.user_capabilities.edit = false;
    ApplicationsAPI.read.mockResolvedValue(applications);
    ApplicationsAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationsList />);
    });
    waitForElement(wrapper, 'ApplicationsList', el => el.length > 0);
    expect(
      wrapper
        .find('ApplicationListItem')
        .at(0)
        .find('PencilAltIcon').length
    ).toBe(0);
    expect(
      wrapper
        .find('ApplicationListItem')
        .at(1)
        .find('PencilAltIcon').length
    ).toBe(1);
  });
});
