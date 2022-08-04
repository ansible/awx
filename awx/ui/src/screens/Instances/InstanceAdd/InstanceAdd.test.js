import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InstancesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InstanceAdd from './InstanceAdd';

jest.mock('../../../api');

describe('<InstanceAdd />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({ initialEntries: ['/instances'] });
    InstancesAPI.create.mockResolvedValue({ data: { id: 13 } });
    await act(async () => {
      wrapper = mountWithContexts(<InstanceAdd />, {
        context: { router: { history } },
      });
    });
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('handleSubmit should call the api and redirect to details page', async () => {
    await waitForElement(wrapper, 'isLoading', (el) => el.length === 0);
    await act(async () => {
      wrapper.find('InstanceForm').prop('handleSubmit')({
        name: 'new Foo',
        node_type: 'hop',
      });
    });
    expect(InstancesAPI.create).toHaveBeenCalledWith({
      name: 'new Foo',
      node_type: 'hop',
    });
    expect(history.location.pathname).toBe('/instances/13/details');
  });

  test('handleCancel should return the user back to the instances list', async () => {
    await waitForElement(wrapper, 'isLoading', (el) => el.length === 0);
    await act(async () => {
      wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual('/instances');
  });
});
