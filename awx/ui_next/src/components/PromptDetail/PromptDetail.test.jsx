import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';

import PromptDetail from './PromptDetail';

const mockTemplate = {
  name: 'Mock Template',
  description: 'mock description',
  unified_job_type: 'job',
  created: '2019-08-08T19:24:05.344276Z',
  modified: '2019-08-08T19:24:18.162949Z',
};

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
    job_tags: 'one,two,three',
    skip_tags: 'skip',
    job_type: 'run',
    verbosity: 1,
    inventory: {
      name: 'Demo Inventory',
      id: 1,
    },
    credentials: [
      {
        id: 1,
        name: 'Demo Credential',
        credential_type: 1,
        passwords_needed: [],
      },
    ],
    scm_branch: '123',
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

      expect(wrapper.find('PromptDetail h2').text()).toBe('Prompted Values');
      assertDetail('Name', 'Mock Template');
      assertDetail('Description', 'mock description');
      assertDetail('Type', 'job');
      assertDetail('Job Type', 'run');
      assertDetail('Credential', 'Demo Credential');
      assertDetail('Inventory', 'Demo Inventory');
      assertDetail('SCM Branch', '123');
      assertDetail('Limit', '3');
      assertDetail('Verbosity', '1 (Verbose)');
      assertDetail('Job Tags', 'onetwothree');
      assertDetail('Skip Tags', 'skip');
      assertDetail('Diff Mode', 'Off');
      expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
        '---foo: bar'
      );
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
      function assertNoDetail(label) {
        expect(wrapper.find(`Detail[label="${label}"]`).length).toBe(0);
      }
      [
        'Job Type',
        'Credential',
        'Inventory',
        'SCM Branch',
        'Limit',
        'Verbosity',
        'Job Tags',
        'Skip Tags',
        'Diff Mode',
      ].forEach(label => assertNoDetail(label));
      expect(wrapper.find('PromptDetail h2').length).toBe(0);
      expect(wrapper.find('VariablesDetail').length).toBe(0);
    });
  });
});
