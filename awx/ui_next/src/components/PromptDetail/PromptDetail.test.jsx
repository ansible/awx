import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import mockTemplate from './data.job_template.json';

import PromptDetail from './PromptDetail';

const mockPromptLaunch = {
  ask_credential_on_launch: true,
  ask_diff_mode_on_launch: true,
  ask_inventory_on_launch: true,
  ask_job_type_on_launch: true,
  ask_limit_on_launch: true,
  ask_scm_branch_on_launch: true,
  ask_skip_tags_on_launch: true,
  ask_tags_on_launch: true,
  ask_variables_on_launch: true,
  ask_verbosity_on_launch: true,
  defaults: {
    extra_vars: '---foo: bar',
    diff_mode: false,
    limit: 3,
    job_tags: 'T_100,T_200',
    skip_tags: 'S_100,S_200',
    job_type: 'run',
    verbosity: 3,
    inventory: {
      name: 'Demo Inventory',
      id: 1,
    },
    credentials: [
      {
        id: 1,
        kind: 'ssh',
        name: 'Credential 1',
      },
      {
        id: 2,
        kind: 'awx',
        name: 'Credential 2',
      },
    ],
    scm_branch: 'Foo branch',
  },
};

describe('PromptDetail', () => {
  describe('With prompt values', () => {
    let wrapper;

    beforeAll(() => {
      wrapper = mountWithContexts(
        <PromptDetail launchConfig={mockPromptLaunch} resource={mockTemplate} />
      );
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('should render successfully', () => {
      expect(wrapper.find('PromptDetail').length).toBe(1);
    });

    test('should render expected details', () => {
      function assertDetail(label, value) {
        expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
        expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
      }

      expect(wrapper.find('PromptDetail h2')).toHaveLength(0);
      assertDetail('Name', 'Mock JT');
      assertDetail('Description', 'Mock JT Description');
      assertDetail('Type', 'Job Template');
      assertDetail('Job Type', 'Run');
      assertDetail('Inventory', 'Demo Inventory');
      assertDetail('Source Control Branch', 'Foo branch');
      assertDetail('Limit', 'alpha:beta');
      assertDetail('Verbosity', '3 (Debug)');
      assertDetail('Show Changes', 'Off');
      expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
        '---foo: bar'
      );
      expect(
        wrapper
          .find('Detail[label="Credentials"]')
          .containsAllMatchingElements([
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
          .find('Detail[label="Job Tags"]')
          .containsAnyMatchingElements([<span>T_100</span>, <span>T_200</span>])
      ).toEqual(true);
      expect(
        wrapper
          .find('Detail[label="Skip Tags"]')
          .containsAllMatchingElements([<span>S_100</span>, <span>S_200</span>])
      ).toEqual(true);
    });
  });

  describe('Without prompt values', () => {
    let wrapper;
    beforeAll(() => {
      wrapper = mountWithContexts(<PromptDetail resource={mockTemplate} />);
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('should render basic detail values', () => {
      expect(wrapper.find(`Detail[label="Name"]`).length).toBe(1);
      expect(wrapper.find(`Detail[label="Description"]`).length).toBe(1);
      expect(wrapper.find(`Detail[label="Type"]`).length).toBe(1);
    });

    test('should not render promptable details', () => {
      const overrideDetails = wrapper.find(
        'DetailList[aria-label="Prompt Overrides"]'
      );
      function assertNoDetail(label) {
        expect(overrideDetails.find(`Detail[label="${label}"]`).length).toBe(0);
      }
      [
        'Job Type',
        'Credential',
        'Inventory',
        'Source Control Branch',
        'Limit',
        'Verbosity',
        'Job Tags',
        'Skip Tags',
        'Diff Mode',
      ].forEach(label => assertNoDetail(label));
      expect(overrideDetails.find('PromptDetail h2').length).toBe(0);
      expect(overrideDetails.find('VariablesDetail').length).toBe(0);
    });
  });

  describe('with overrides', () => {
    let wrapper;
    const overrides = {
      extra_vars: '---one: two\nbar: baz',
      inventory: {
        name: 'Override inventory',
      },
    };

    beforeAll(() => {
      wrapper = mountWithContexts(
        <PromptDetail
          launchConfig={mockPromptLaunch}
          resource={{
            ...mockTemplate,
            ask_inventory_on_launch: true,
          }}
          overrides={overrides}
        />
      );
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('should render overridden details', () => {
      function assertDetail(label, value) {
        expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
        expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
      }

      expect(wrapper.find('PromptDetail h2').text()).toBe('Prompted Values');
      assertDetail('Name', 'Mock JT');
      assertDetail('Description', 'Mock JT Description');
      assertDetail('Type', 'Job Template');
      assertDetail('Job Type', 'Run');
      assertDetail('Inventory', 'Override inventory');
      assertDetail('Source Control Branch', 'Foo branch');
      assertDetail('Limit', 'alpha:beta');
      assertDetail('Verbosity', '3 (Debug)');
      assertDetail('Show Changes', 'Off');
      expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
        '---one: two\nbar: baz'
      );
      expect(
        wrapper
          .find('Detail[label="Credentials"]')
          .containsAllMatchingElements([
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
          .find('Detail[label="Job Tags"]')
          .containsAnyMatchingElements([<span>T_100</span>, <span>T_200</span>])
      ).toEqual(true);
      expect(
        wrapper
          .find('Detail[label="Skip Tags"]')
          .containsAllMatchingElements([<span>S_100</span>, <span>S_200</span>])
      ).toEqual(true);
    });
  });
});
