import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import PromptJobTemplateDetail from './PromptJobTemplateDetail';
import mockData from './data.job_template.json';

const mockJT = {
  ...mockData,
  instance_groups: [
    {
      id: 1,
      name: 'ig1',
    },
    {
      id: 2,
      name: 'ig2',
    },
  ],
};

describe('PromptJobTemplateDetail', () => {
  let wrapper;

  beforeAll(() => {
    wrapper = mountWithContexts(<PromptJobTemplateDetail resource={mockJT} />);
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('should render successfully', () => {
    expect(wrapper.find('PromptJobTemplateDetail')).toHaveLength(1);
  });

  test('should render expected details', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Job Type', 'Run');
    assertDetail('Inventory', 'Demo Inventory');
    assertDetail('Project', 'Mock Project');
    assertDetail('Source Control Branch', 'Foo branch');
    assertDetail('Playbook', 'ping.yml');
    assertDetail('Forks', '2');
    assertDetail('Limit', 'alpha:beta');
    assertDetail('Verbosity', '3 (Debug)');
    assertDetail('Show Changes', 'Off');
    assertDetail('Job Slicing', '1');
    assertDetail('Host Config Key', 'a1b2c3');
    expect(
      wrapper.find('Detail[label="Provisioning Callback URL"] dd').text()
    ).toEqual(expect.stringContaining('/api/v2/job_templates/7/callback/'));
    expect(
      wrapper.find('Detail[label="Credentials"]').containsAllMatchingElements([
        <span>
          <strong>SSH:</strong>Credential 1
        </span>,
        <span>
          <strong>Awx:</strong>Credential 2
        </span>,
      ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Labels"]')
        .containsAllMatchingElements([<span>L_91o2</span>, <span>L_91o3</span>])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Instance Groups"]')
        .containsAllMatchingElements([<span>ig1</span>, <span>ig2</span>])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Job Tags"]')
        .containsAllMatchingElements([<span>T_100</span>, <span>T_200</span>])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Skip Tags"]')
        .containsAllMatchingElements([<span>S_100</span>, <span>S_200</span>])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Enable Privilege Escalation</li>,
          <li>Allow Provisioning Callbacks</li>,
          <li>Enable Concurrent Jobs</li>,
          <li>Use Fact Storage</li>,
        ])
    ).toEqual(true);
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---foo: bar'
    );
  });
});
