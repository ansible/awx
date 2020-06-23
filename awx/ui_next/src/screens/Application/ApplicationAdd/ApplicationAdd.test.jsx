import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import { ApplicationsAPI } from '../../../api';
import ApplicationAdd from './ApplicationAdd';

jest.mock('../../../api/models/Applications');
jest.mock('../../../api/models/Organizations');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  history: () => ({
    location: '/applications/add',
  }),
}));
const options = {
  data: {
    actions: {
      GET: {
        client_type: {
          choices: [
            ['confidential', 'Confidential'],
            ['public', 'Public'],
          ],
        },
        authorization_grant_type: {
          choices: [
            ['authorization-code', 'Authorization code'],
            ['password', 'Resource owner password-based'],
          ],
        },
      },
    },
  },
};

describe('<ApplicationAdd/>', () => {
  let wrapper;
  test('should render properly', async () => {
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationAdd />);
    });
    expect(wrapper.find('ApplicationAdd').length).toBe(1);
    expect(wrapper.find('ApplicationForm').length).toBe(1);
    expect(ApplicationsAPI.readOptions).toBeCalled();
  });

  test('expect values to be updated and submitted properly', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/applications/add'],
    });
    ApplicationsAPI.readOptions.mockResolvedValue(options);

    ApplicationsAPI.create.mockResolvedValue({ data: { id: 8 } });
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationAdd />, {
        context: { router: { history } },
      });
    });

    await act(async () => {
      wrapper.find('input#name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      wrapper.find('input#description').simulate('change', {
        target: { value: 'new bar', name: 'description' },
      });
      wrapper
        .find('AnsibleSelect[name="authorization_grant_type"]')
        .prop('onChange')({}, 'authorization code');

      wrapper.find('input#redirect_uris').simulate('change', {
        target: { value: 'https://www.google.com', name: 'redirect_uris' },
      });
      wrapper.find('AnsibleSelect[name="client_type"]').prop('onChange')(
        {},
        'confidential'
      );
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 1,
        name: 'organization',
      });
    });

    wrapper.update();
    expect(wrapper.find('input#name').prop('value')).toBe('new foo');
    expect(wrapper.find('input#description').prop('value')).toBe('new bar');
    expect(wrapper.find('Chip').length).toBe(1);
    expect(wrapper.find('Chip').text()).toBe('organization');
    expect(
      wrapper
        .find('AnsibleSelect[name="authorization_grant_type"]')
        .prop('value')
    ).toBe('authorization code');
    expect(
      wrapper.find('AnsibleSelect[name="client_type"]').prop('value')
    ).toBe('confidential');
    expect(wrapper.find('input#redirect_uris').prop('value')).toBe(
      'https://www.google.com'
    );
    await act(async () => {
      wrapper.find('Formik').prop('onSubmit')({
        authorization_grant_type: 'authorization-code',
        client_type: 'confidential',
        description: 'bar',
        name: 'foo',
        organization: { id: 1 },
        redirect_uris: 'http://www.google.com',
      });
    });

    expect(ApplicationsAPI.create).toBeCalledWith({
      authorization_grant_type: 'authorization-code',
      client_type: 'confidential',
      description: 'bar',
      name: 'foo',
      organization: 1,
      redirect_uris: 'http://www.google.com',
    });
    expect(history.location.pathname).toBe('/applications/8/details');
  });

  test('should cancel form properly', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/applications/add'],
    });
    ApplicationsAPI.readOptions.mockResolvedValue(options);

    ApplicationsAPI.create.mockResolvedValue({ data: { id: 8 } });
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationAdd />, {
        context: { router: { history } },
      });
    });
    await act(async () => {
      wrapper.find('Button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toBe('/applications');
  });

  test('should throw error on submit', async () => {
    const error = {
      response: {
        config: {
          method: 'patch',
          url: '/api/v2/applications/',
        },
        data: { detail: 'An error occurred' },
      },
    };
    ApplicationsAPI.create.mockRejectedValue(error);
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationAdd />);
    });
    await act(async () => {
      wrapper.find('Formik').prop('onSubmit')({
        id: 1,
        organization: { id: 1 },
      });
    });

    waitForElement(wrapper, 'FormSubmitError', el => el.length > 0);
  });
  test('should render content error on failed read options request', async () => {
    ApplicationsAPI.readOptions.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'options',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<ApplicationAdd />);
    });

    wrapper.update();
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
