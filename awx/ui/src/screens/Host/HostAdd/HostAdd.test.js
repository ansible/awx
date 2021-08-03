import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { HostsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import HostAdd from './HostAdd';

jest.mock('../../../api');

const hostData = {
  name: 'new name',
  description: 'new description',
  inventory: {
    id: 1,
    name: 'Demo Inventory',
  },
  variables: '---\nfoo: bar',
};

describe('<HostAdd />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/templates/job_templates/1/survey/edit/foo'],
      state: { some: 'state' },
    });
    HostsAPI.create.mockResolvedValue({
      data: {
        ...hostData,
        id: 5,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<HostAdd />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('handleSubmit should post to api', async () => {
    await act(async () => {
      wrapper.find('HostForm').prop('handleSubmit')(hostData);
    });
    expect(HostsAPI.create).toHaveBeenCalledWith({ ...hostData, inventory: 1 });
  });

  test('should navigate to hosts list when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual('/hosts');
  });

  test('successful form submission should trigger redirect', async () => {
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(hostData);
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual('/hosts/5/details');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    HostsAPI.create.mockImplementationOnce(() => Promise.reject(error));
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(hostData);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
