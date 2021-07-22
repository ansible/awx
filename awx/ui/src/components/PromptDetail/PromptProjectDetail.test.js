import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PromptProjectDetail from './PromptProjectDetail';
import mockProject from './data.project.json';

function assertDetail(wrapper, label, value) {
  expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
  expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
}

describe('PromptProjectDetail', () => {
  let wrapper;
  const config = {
    project_base_dir: 'dir/foo/bar',
  };

  beforeAll(() => {
    wrapper = mountWithContexts(
      <PromptProjectDetail
        resource={{ ...mockProject, scm_track_submodules: true }}
      />,
      {
        context: { config },
      }
    );
  });

  test('should render successfully', () => {
    expect(wrapper.find('PromptProjectDetail')).toHaveLength(1);
  });

  test('should render expected details', () => {
    assertDetail(wrapper, 'Source Control Type', 'Git');
    assertDetail(
      wrapper,
      'Source Control URL',
      'https://github.com/ansible/ansible-tower-samples'
    );
    assertDetail(wrapper, 'Source Control Branch', 'foo');
    assertDetail(wrapper, 'Source Control Refspec', 'refs/');
    assertDetail(wrapper, 'Cache Timeout', '3 Seconds');
    assertDetail(wrapper, 'Project Base Path', 'dir/foo/bar');
    assertDetail(wrapper, 'Playbook Directory', '_6__demo_project');
    assertDetail(wrapper, 'Source Control Credential', 'Scm: mock scm');
    const executionEnvironment = wrapper.find('ExecutionEnvironmentDetail');
    expect(executionEnvironment).toHaveLength(1);
    expect(executionEnvironment.find('dt').text()).toEqual(
      'Default Execution Environment'
    );
    expect(executionEnvironment.find('dd').text()).toEqual(
      mockProject.summary_fields.default_environment.name
    );
    expect(
      wrapper
        .find('Detail[label="Enabled Options"]')
        .containsAllMatchingElements([
          <li>Discard local changes before syncing</li>,
          <li>Delete the project before syncing</li>,
          <li>Track submodules latest commit on branch</li>,
          <li>Update revision on job launch</li>,
          <li>Allow branch override</li>,
        ])
    ).toEqual(true);
  });

  test('should render "Deleted" details', () => {
    delete mockProject.summary_fields.organization;
    wrapper = mountWithContexts(
      <PromptProjectDetail resource={mockProject} />,
      {
        context: { config },
      }
    );
    assertDetail(wrapper, 'Organization', 'Deleted');
  });
});
