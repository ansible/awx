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

    expect(history.location.search).toEqual('?stdout__icontains=99');
  });
});
