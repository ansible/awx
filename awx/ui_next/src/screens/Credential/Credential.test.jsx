import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { CredentialsAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockCredential from './shared/data.scmCredential.json';
import mockOrgCredential from './shared/data.orgCredential.json';
import Credential from './Credential';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/credentials/2',
    params: { id: 2 },
  }),
}));

CredentialsAPI.readDetail.mockResolvedValueOnce({
  data: mockCredential,
});

describe('<Credential />', () => {
  let wrapper;

  test('initially renders user-based credential succesfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<Credential setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 2);
  });

  test('initially renders org-based credential succesfully', async () => {
    CredentialsAPI.readDetail.mockResolvedValueOnce({
      data: mockOrgCredential,
    });

    await act(async () => {
      wrapper = mountWithContexts(<Credential setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    // org-based credential detail needs access tab
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 3);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/credentials/2/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Credential setBreadcrumb={() => {}} />, {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/credentials/2/foobar',
                path: '/credentials/2/foobar',
              },
            },
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
