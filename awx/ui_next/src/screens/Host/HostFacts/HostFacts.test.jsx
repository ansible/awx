import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import HostFacts from './HostFacts';
import { HostsAPI } from '../../../api';
import mockHost from '../data.host.json';
import mockHostFacts from '../data.hostFacts.json';

jest.mock('../../../api/models/Hosts');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    hostId: 1,
  }),
}));

describe('<HostFacts />', () => {
  let wrapper;

  beforeEach(async () => {
    HostsAPI.readFacts.mockResolvedValue({ data: mockHostFacts });
    await act(async () => {
      wrapper = mountWithContexts(<HostFacts host={mockHost} />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders successfully ', () => {
    expect(wrapper.find('HostFacts').length).toBe(1);
  });

  test('renders ContentError when facts GET fails', async () => {
    HostsAPI.readFacts.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/hosts/1/ansible_facts',
          },
          data: 'An error occurred',
          status: 500,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<HostFacts host={mockHost} />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
