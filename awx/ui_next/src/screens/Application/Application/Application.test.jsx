import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { ApplicationsAPI } from '../../../api';
import Application from './Application';

jest.mock('../../../api/models/Applications');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  history: () => ({
    location: '/applications',
  }),
  useParams: () => ({ id: 1 }),
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
const application = {
  id: 1,
  name: 'Foo',
  summary_fields: {
    organization: { name: 'Org 1', id: 10 },
    user_capabilities: { edit: true, delete: true },
  },
  url: '',
  organization: 10,
};
describe('<Application />', () => {
  let wrapper;
  test('mounts properly', async () => {
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    ApplicationsAPI.readDetail.mockResolvedValue(application);
    await act(async () => {
      wrapper = mountWithContexts(<Application setBreadcrumb={() => {}} />);
    });
    expect(wrapper.find('Application').length).toBe(1);
    expect(ApplicationsAPI.readOptions).toBeCalled();
    expect(ApplicationsAPI.readDetail).toBeCalledWith(1);
  });
  test('should throw error', async () => {
    ApplicationsAPI.readOptions.mockResolvedValue(options);
    ApplicationsAPI.readDetail.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/applications/1',
          },
          data: 'An error occurred',
          status: 404,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<Application setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
    expect(wrapper.find('ApplicationAdd').length).toBe(0);
    expect(wrapper.find('ApplicationDetails').length).toBe(0);
    expect(wrapper.find('Application').length).toBe(1);
    expect(ApplicationsAPI.readOptions).toBeCalled();
    expect(ApplicationsAPI.readDetail).toBeCalledWith(1);
  });
});
