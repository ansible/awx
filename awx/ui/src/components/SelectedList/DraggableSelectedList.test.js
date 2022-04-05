// These tests have been turned off because they fail due to a console wanring coming from patternfly.
//  The warning is that the onDrag api has been deprecated.  It's replacement is a DragDrop component,
// however that component is not keyboard accessible.  Therefore we have elected to turn off these tests.
//github.com/patternfly/patternfly-react/issues/6317s

import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DraggableSelectedList from './DraggableSelectedList';

describe.skip('<DraggableSelectedList />', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render expected rows', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
      {
        id: 2,
        name: 'bar',
      },
    ];
    wrapper = mountWithContexts(
      <DraggableSelectedList
        selected={mockSelected}
        onRemove={() => {}}
        onRowDrag={() => {}}
      />
    );
    expect(wrapper.find('DraggableSelectedList').length).toBe(1);
    expect(wrapper.find('DataListItem').length).toBe(2);
    expect(
      wrapper
        .find('DataListItem DataListCell')
        .first()
        .containsMatchingElement(<span>1. foo</span>)
    ).toEqual(true);
    expect(
      wrapper
        .find('DataListItem DataListCell')
        .last()
        .containsMatchingElement(<span>2. bar</span>)
    ).toEqual(true);
  });

  test('should not render when selected list is empty', () => {
    wrapper = mountWithContexts(
      <DraggableSelectedList
        selected={[]}
        onRemove={() => {}}
        onRowDrag={() => {}}
      />
    );
    expect(wrapper.find('DataList').length).toBe(0);
  });

  test('should call onRemove callback prop on remove button click', () => {
    const onRemove = jest.fn();
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
    ];
    wrapper = mountWithContexts(
      <DraggableSelectedList selected={mockSelected} onRemove={onRemove} />
    );
    expect(
      wrapper
        .find('DataListDragButton[aria-label="Reorder"]')
        .prop('isDisabled')
    ).toBe(true);
    wrapper
      .find('DataListItem[id="foo"] Button[aria-label="Remove"]')
      .simulate('click');
    expect(onRemove).toBeCalledWith({
      id: 1,
      name: 'foo',
    });
  });

  test('should disable remove button when dragging item', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
      {
        id: 2,
        name: 'bar',
      },
    ];
    wrapper = mountWithContexts(
      <DraggableSelectedList
        selected={mockSelected}
        onRemove={() => {}}
        onRowDrag={() => {}}
      />
    );

    expect(
      wrapper.find('Button[aria-label="Remove"]').at(0).prop('isDisabled')
    ).toBe(false);
    expect(
      wrapper.find('Button[aria-label="Remove"]').at(1).prop('isDisabled')
    ).toBe(false);
    act(() => {
      wrapper.find('DataList').prop('onDragStart')();
    });
    wrapper.update();
    expect(
      wrapper.find('Button[aria-label="Remove"]').at(0).prop('isDisabled')
    ).toBe(true);
    expect(
      wrapper.find('Button[aria-label="Remove"]').at(1).prop('isDisabled')
    ).toBe(true);
    act(() => {
      wrapper.find('DataList').prop('onDragCancel')();
    });
    wrapper.update();
    expect(
      wrapper.find('Button[aria-label="Remove"]').at(0).prop('isDisabled')
    ).toBe(false);
    expect(
      wrapper.find('Button[aria-label="Remove"]').at(1).prop('isDisabled')
    ).toBe(false);
  });
});
