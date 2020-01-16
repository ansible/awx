import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { CredentialsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { mockCredentials } from './shared';
import Credential from './Credential';

jest.mock('@api');

CredentialsAPI.readDetail.mockResolvedValue({
  data: mockCredentials.results[0],
});

describe('<Credential />', () => {
  let wrapper;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(<Credential setBreadcrumb={() => {}} />);
    });
  });

  test('initially renders succesfully', async () => {
    expect(wrapper.find('Credential').length).toBe(1);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/credentials/1/foobar'],
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
                url: '/credentials/1/foobar',
                path: '/credentials/1/foobar',
              },
            },
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual('Not Found');
  });

  test('should show content error if api throws an error', async () => {
    CredentialsAPI.readDetail.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<Credential setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual(
      'Something went wrong...'
    );
  });
});
