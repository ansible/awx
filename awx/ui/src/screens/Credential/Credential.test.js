import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { CredentialsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockMachineCredential from './shared/data.machineCredential.json';
import mockSCMCredential from './shared/data.scmCredential.json';
import mockCyberArkCredential from './shared/data.cyberArkCredential.json';
import Credential from './Credential';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/credentials/2',
    params: { id: 2 },
  }),
}));

describe('<Credential />', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();

    wrapper.unmount();
  });

  test('initially renders user-based machine credential successfully', async () => {
    CredentialsAPI.readDetail.mockResolvedValueOnce({
      data: mockMachineCredential,
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Credential setBreadcrumb={() => {}} buildActivityStream={() => {}} />
      );
    });
    wrapper.update();
    expect(wrapper.find('Credential').length).toBe(1);
    expect(wrapper.find('RoutedTabs li').length).toBe(4);
  });

  test('initially renders user-based SCM credential successfully', async () => {
    CredentialsAPI.readDetail.mockResolvedValueOnce({
      data: mockSCMCredential,
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Credential setBreadcrumb={() => {}} buildActivityStream={() => {}} />
      );
    });
    wrapper.update();
    expect(wrapper.find('Credential').length).toBe(1);
    expect(wrapper.find('RoutedTabs li').length).toBe(3);
  });

  test('should render expected tabs', async () => {
    const expectedTabs = [
      'Back to Credentials',
      'Details',
      'Access',
      'Job Templates',
    ];
    await act(async () => {
      wrapper = mountWithContexts(
        <Credential setBreadcrumb={() => {}} buildActivityStream={() => {}} />
      );
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should not render job template tab', async () => {
    CredentialsAPI.readDetail.mockResolvedValueOnce({
      data: { ...mockCyberArkCredential, kind: 'registry' },
    });
    const expectedTabs = ['Back to Credentials', 'Details', 'Access'];
    await act(async () => {
      wrapper = mountWithContexts(
        <Credential setBreadcrumb={() => {}} buildActivityStream={() => {}} />
      );
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/credentials/2/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Credential setBreadcrumb={() => {}} buildActivityStream={() => {}} />,
        {
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
        }
      );
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
describe('<Credential> should not show job template tab', () => {});
