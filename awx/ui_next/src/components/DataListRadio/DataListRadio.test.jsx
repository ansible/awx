import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import DataListRadio from './DataListRadio';

describe('DataListRadio', () => {
  test('should call onChange', () => {
    const onChange = jest.fn();
    const wrapper = mountWithContexts(<DataListRadio onChange={onChange} />);
    wrapper.find('input[type="radio"]').prop('onChange')({
      currentTarget: { checked: true },
    });
    expect(onChange).toHaveBeenCalledWith(true, {
      currentTarget: { checked: true },
    });
  });

  test('should pass props to correct children', () => {
    const onChange = jest.fn();
    const wrapper = mountWithContexts(
      <DataListRadio
        onChange={onChange}
        className="foo"
        isValid
        isDisabled
        checked
      />
    );
    const div = wrapper.find('.pf-c-data-list__item-control');
    const input = wrapper.find('input[type="radio"]');

    expect(div.prop('className')).toEqual('pf-c-data-list__item-control foo');
    expect(input.prop('disabled')).toBe(true);
    expect(input.prop('checked')).toBe(true);
    expect(input.prop('aria-invalid')).toBe(false);
  });
});
