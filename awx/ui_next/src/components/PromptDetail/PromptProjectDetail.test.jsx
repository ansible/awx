import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import PromptProjectDetail from './PromptProjectDetail';
import mockProject from './data.project.json';

describe('PromptProjectDetail', () => {
  let wrapper;

  beforeAll(() => {
    const config = {
      project_base_dir: 'dir/foo/bar',
    };
    wrapper = mountWithContexts(
      <PromptProjectDetail resource={mockProject} />,
      {
        context: { config },
      }
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('should render successfully', () => {
    expect(wrapper.find('PromptProjectDetail')).toHaveLength(1);
  });

  test('should render expected details', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('SCM Type', 'Git');
    assertDetail('SCM URL', 'https://github.com/ansible/ansible-tower-samples');
    assertDetail('SCM Branch', 'foo');
    assertDetail('SCM Refspec', 'refs/');
    assertDetail('Cache Timeout', '3 Seconds');
    assertDetail('Ansible Environment', 'mock virtual env');
    assertDetail('Project Base Path', 'dir/foo/bar');
    assertDetail('Playbook Directory', '_6__demo_project');
    assertDetail('SCM Credential', 'Scm: mock scm');
    expect(
      wrapper
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Clean</li>,
          <li>Delete on Update</li>,
          <li>Update Revision on Launch</li>,
          <li>Allow Branch Override</li>,
        ])
    ).toEqual(true);
  });
});
