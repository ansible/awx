import React from 'react';
import { act } from 'react-dom/test-utils';
import { RootAPI } from 'api';
import * as SessionContext from 'contexts/Session';
import { mountWithContexts } from '../testUtils/enzymeHelpers';
import App from './App';

jest.mock('./api');

describe('<App />', () => {
  beforeEach(() => {
    RootAPI.readAssetVariables.mockResolvedValue({
      data: {
        BRAND_NAME: 'AWX',
      },
    });
  });

  test('renders ok', async () => {
    const contextValues = {
      setAuthRedirectTo: jest.fn(),
      isSessionExpired: false,
    };
    jest
      .spyOn(SessionContext, 'useSession')
      .mockImplementation(() => contextValues);

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<App />);
    });
    expect(wrapper.length).toBe(1);
    jest.clearAllMocks();
  });
});
