import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import ProjectAdd from './ProjectAdd';
import { ProjectsAPI } from '@api';

jest.mock('@api');

describe('<ProjectAdd />', () => {
  const projectData = {
    name: 'foo',
    description: 'bar',
    scm_type: 'git',
    scm_url: 'https://foo.bar',
    scm_clean: true,
    credential: 100,
    organization: 2,
    scm_update_on_launch: true,
    scm_update_cache_timeout: 3,
    allow_override: false,
    custom_virtualenv: '/venv/custom-env',
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    const wrapper = mountWithContexts(<ProjectAdd />);
    expect(wrapper.length).toBe(1);
  });

  test('handleSubmit should post to the api', async () => {
    ProjectsAPI.create.mockResolvedValueOnce({
      data: { ...projectData },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectAdd />);
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      formik.setState(
        {
          values: {
            ...projectData,
          },
        },
        () => resolve()
      );
    });
    await changeState;
    wrapper.find('form').simulate('submit');
  });

  test('handleSubmit should throw an error', async () => {
    ProjectsAPI.create.mockImplementation(() => Promise.reject(new Error()));
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectAdd />);
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      formik.setState(
        {
          values: {
            ...projectData,
          },
        },
        () => resolve()
      );
    });
    await changeState;
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    wrapper.update();
    expect(wrapper.find('ProjectAdd .formSubmitError').length).toBe(1);
  });

  test('CardHeader close button should navigate to projects list', () => {
    const history = createMemoryHistory();
    const wrapper = mountWithContexts(<ProjectAdd />, {
      context: { router: { history } },
    }).find('ProjectAdd CardHeader');
    wrapper.find('CardCloseButton').simulate('click');
    expect(history.location.pathname).toEqual('/projects');
  });

  test('CardBody cancel button should navigate to projects list', () => {
    const history = createMemoryHistory();
    const wrapper = mountWithContexts(<ProjectAdd />, {
      context: { router: { history } },
    }).find('ProjectAdd CardBody');
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/projects');
  });
});
