import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { CredentialTypesAPI } from '../../api';

import CredentialType from './CredentialType';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/credential_types',
  }),
  useParams: () => ({ id: 42 }),
}));

describe('<CredentialType/>', () => {
  let wrapper;
  test('should render details properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<CredentialType setBreadcrumb={() => {}} />);
    });
    wrapper.update();
    expect(wrapper.find('CredentialType').length).toBe(1);
    expect(CredentialTypesAPI.readDetail).toBeCalledWith(42);
  });

  test('should render expected tabs', async () => {
    const expectedTabs = ['Back to credential types', 'Details'];
    await act(async () => {
      wrapper = mountWithContexts(<CredentialType setBreadcrumb={() => {}} />);
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/credential_types/42/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<CredentialType setBreadcrumb={() => {}} />, {
        context: {
          router: {
            history,
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
