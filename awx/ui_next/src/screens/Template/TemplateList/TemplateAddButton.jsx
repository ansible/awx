import React, { useState, useRef, useEffect } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Dropdown, DropdownPosition } from '@patternfly/react-core';
import { ToolbarAddButton } from '@components/PaginatedDataList';

function TemplateAddButton({ match, i18n }) {
  const [isOpen, setIsOpen] = useState(false);
  const element = useRef(null);

  const toggle = e => {
    if (!element || !element.current.contains(e.target)) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', toggle, false);
    return () => {
      document.removeEventListener('click', toggle);
    };
  }, []);

  return (
    <div ref={element} key="add">
      <Dropdown
        isPlain
        isOpen={isOpen}
        position={DropdownPosition.right}
        toggle={<ToolbarAddButton onClick={() => setIsOpen(!isOpen)} />}
        dropdownItems={[
          <Link
            key="job"
            className="pf-c-dropdown__menu-item"
            to={`${match.url}/job_template/add/`}
          >
            {i18n._(t`Job Template`)}
          </Link>,
          <Link
            key="workflow"
            className="pf-c-dropdown__menu-item"
            to={`${match.url}_workflow/add/`}
          >
            {i18n._(t`Workflow Template`)}
          </Link>,
        ]}
      />
    </div>
  );
}

export { TemplateAddButton as _TemplateAddButton };
export default withI18n()(withRouter(TemplateAddButton));
