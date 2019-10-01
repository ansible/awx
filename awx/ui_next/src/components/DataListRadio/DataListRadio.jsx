import * as React from 'react';
import { string, bool, func } from 'prop-types';

function DataListRadio({
  className = '',
  onChange,
  isValid = true,
  isDisabled = false,
  isChecked = null,
  checked = null,
  ...props
}) {
  return (
    <div className={`pf-c-data-list__item-control ${className}`}>
      <div className="pf-c-data-list__check">
        <input
          {...props}
          type="radio"
          onChange={event => onChange(event.currentTarget.checked, event)}
          aria-invalid={!isValid}
          disabled={isDisabled}
          checked={isChecked || checked}
        />
      </div>
    </div>
  );
}
DataListRadio.propTypes = {
  className: string,
  isValid: bool,
  isDisabled: bool,
  isChecked: bool,
  checked: bool,
  onChange: func,
  'aria-labelledby': string,
};
DataListRadio.defaultProps = {
  className: '',
  isValid: true,
  isDisabled: false,
  isChecked: false,
  checked: false,
  onChange: () => {},
  'aria-labelledby': '',
};

export default DataListRadio;
