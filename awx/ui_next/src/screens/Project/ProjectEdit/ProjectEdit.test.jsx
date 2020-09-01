import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import ProjectEdit from './ProjectEdit';
import { ProjectsAPI, CredentialTypesAPI } from '../../../api';

jest.mock('../../../api');

describe('<ProjectEdit />', () => {
  let wrapper;
  const projectData = {
    id: 123,
    name: 'foo',
    description: 'bar',
    scm_type: 'git',
    scm_url: 'https://foo.bar',
    scm_clean: true,
    credential: 100,
    local_path: 'bar',
    organization: 2,
    scm_update_on_launch: true,
    scm_update_cache_timeout: 3,
    allow_override: false,
    custom_virtualenv: '/venv/custom-env',
    summary_fields: {
      credential: {
        id: 100,
        credential_type_id: 5,
        kind: 'insights',
      },
      organization: {
        id: 2,
        name: 'Default',
      },
    },
  };

  const projectOptionsResolve = {
    data: {
      actions: {
        GET: {
          scm_type: {
            choices: [
              ['', 'Manual'],
              ['git', 'Git'],
              ['hg', 'Mercurial'],
              ['svn', 'Subversion'],
              ['archive', 'Remote Archive'],
              ['insights', 'Red Hat Insights'],
            ],
          },
        },
      },
    },
  };

  const scmCredentialResolve = {
    data: {
      results: [
        {
          id: 4,
          name: 'Source Control',
          kind: 'scm',
        },
      ],
    },
  };

  const insightsCredentialResolve = {
    data: {
      results: [
        {
          id: 5,
          name: 'Insights',
          kind: 'insights',
        },
      ],
    },
  };

  beforeEach(async () => {
    await ProjectsAPI.readOptions.mockImplementation(
      () => projectOptionsResolve
    );
    await CredentialTypesAPI.read.mockImplementationOnce(
      () => scmCredentialResolve
    );
    await CredentialTypesAPI.read.mockImplementationOnce(
      () => insightsCredentialResolve
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ProjectEdit project={projectData} />);
    });
    expect(wrapper.length).toBe(1);
  });

  test('handleSubmit should post to the api', async () => {
    const history = createMemoryHistory();
    ProjectsAPI.update.mockResolvedValueOnce({
      data: { ...projectData },
    });
    await act(async () => {
      wrapper = mountWithContexts(<ProjectEdit project={projectData} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    wrapper.update();
    expect(ProjectsAPI.update).toHaveBeenCalledTimes(1);
  });

  test('handleSubmit should throw an error', async () => {
    const config = {
      project_local_paths: [],
      project_base_dir: 'foo/bar',
    };
    const error = new Error('oops');
    const realConsoleError = global.console.error;
    global.console.error = jest.fn();
    ProjectsAPI.update.mockImplementation(() => Promise.reject(error));
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectEdit project={{ ...projectData, scm_type: 'manual' }} />,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    wrapper.update();
    expect(ProjectsAPI.update).toHaveBeenCalledTimes(1);
    expect(wrapper.find('ProjectForm').prop('submitError')).toEqual(error);
    global.console.error = realConsoleError;
  });

  test('CardBody cancel button should navigate to project details', async () => {
    const history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(<ProjectEdit project={projectData} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    await act(async () => {
      wrapper.find('ProjectEdit button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual('/projects/123/details');
  });
});
