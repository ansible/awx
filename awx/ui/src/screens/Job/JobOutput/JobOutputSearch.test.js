import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import JobOutputSearch from './JobOutputSearch';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  history: () => ({
    location: '/jobs/playbook/1/output',
  }),
}));

describe('JobOutputSearch', () => {
  test('should update url query params', async () => {
    const searchBtn = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const history = createMemoryHistory({
      initialEntries: ['/jobs/playbook/1/output'],
    });

    const wrapper = mountWithContexts(
      <JobOutputSearch
        job={{
          status: 'successful',
          type: 'project',
        }}
        qsConfig={{
          defaultParams: { page: 1 },
          integerFields: ['page', 'page_size'],
        }}
      />,
      {
        context: { router: { history } },
      }
    );

    await act(async () => {
      wrapper.find(searchTextInput).instance().value = '99';
      wrapper.find(searchTextInput).simulate('change');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find(searchBtn).simulate('click');
    });
    expect(wrapper.find('Search').prop('columns')).toHaveLength(3);
    expect(wrapper.find('Search').prop('columns')[0].name).toBe('Stdout');
    expect(wrapper.find('Search').prop('columns')[1].name).toBe('Event');
    expect(wrapper.find('Search').prop('columns')[2].name).toBe('Advanced');
    expect(history.location.search).toEqual('?stdout__icontains=99');
  });
  test('Should not have Event key in search drop down for system job', () => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs/playbook/1/output'],
    });

    const wrapper = mountWithContexts(
      <JobOutputSearch
        job={{
          status: 'successful',
          type: 'system_job',
        }}
        qsConfig={{
          defaultParams: { page: 1 },
          integerFields: ['page', 'page_size'],
        }}
      />,
      {
        context: { router: { history } },
      }
    );
    expect(wrapper.find('Search').prop('columns')).toHaveLength(2);
    expect(wrapper.find('Search').prop('columns')[0].name).toBe('Stdout');
    expect(wrapper.find('Search').prop('columns')[1].name).toBe('Advanced');
  });

  test('Should not have Event key in search drop down for inventory update job', () => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs/playbook/1/output'],
    });

    const wrapper = mountWithContexts(
      <JobOutputSearch
        job={{
          status: 'successful',
          type: 'inventory_update',
        }}
        qsConfig={{
          defaultParams: { page: 1 },
          integerFields: ['page', 'page_size'],
        }}
      />,
      {
        context: { router: { history } },
      }
    );

    expect(wrapper.find('Search').prop('columns')).toHaveLength(2);
    expect(wrapper.find('Search').prop('columns')[0].name).toBe('Stdout');
    expect(wrapper.find('Search').prop('columns')[1].name).toBe('Advanced');
  });
});
