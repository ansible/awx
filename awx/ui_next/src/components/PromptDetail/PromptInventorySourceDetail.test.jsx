import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import PromptInventorySourceDetail from './PromptInventorySourceDetail';
import mockInvSource from './data.inventory_source.json';

describe('PromptInventorySourceDetail', () => {
  let wrapper;

  beforeAll(() => {
    wrapper = mountWithContexts(
      <PromptInventorySourceDetail resource={mockInvSource} />
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('should render successfully', () => {
    expect(wrapper.find('PromptInventorySourceDetail')).toHaveLength(1);
  });

  test('should render expected details', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Inventory', 'Demo Inventory');
    assertDetail('Source', 'scm');
    assertDetail('Project', 'Mock Project');
    assertDetail('Inventory File', 'foo');
    assertDetail('Custom Inventory Script', 'Mock Script');
    assertDetail('Verbosity', '2 (More Verbose)');
    assertDetail('Cache Timeout', '2 Seconds');
    expect(
      wrapper
        .find('Detail[label="Regions"]')
        .containsAllMatchingElements([
          <span>us-east-1</span>,
          <span>us-east-2</span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Instance Filters"]')
        .containsAllMatchingElements([
          <span>filter1</span>,
          <span>filter2</span>,
          <span>filter3</span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Only Group By"]')
        .containsAllMatchingElements([
          <span>group1</span>,
          <span>group2</span>,
          <span>group3</span>,
        ])
    ).toEqual(true);
    expect(wrapper.find('CredentialChip').text()).toBe('Cloud: mock cred');
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---\nfoo: bar'
    );
    expect(
      wrapper
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Overwrite</li>,
          <li>Overwrite Variables</li>,
          <li>Update on Launch</li>,
          <li>Update on Project Update</li>,
        ])
    ).toEqual(true);
  });
});
