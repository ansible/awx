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

    assertDetail('Source Control Type', 'Git');
    assertDetail(
      'Source Control URL',
      'https://github.com/ansible/ansible-tower-samples'
    );
    assertDetail('Source Control Branch', 'foo');
    assertDetail('Source Control Refspec', 'refs/');
    assertDetail('Cache Timeout', '3 Seconds');
    assertDetail('Ansible Environment', 'mock virtual env');
    assertDetail('Project Base Path', 'dir/foo/bar');
    assertDetail('Playbook Directory', '_6__demo_project');
    assertDetail('Source Control Credential', 'Scm: mock scm');
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
