import React from 'react';
import { string } from 'prop-types';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { TimesIcon } from '@patternfly/react-icons';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

function CardCloseButton({ linkTo, i18n, i18nHash, ...props }) {
  if (linkTo) {
    return (
      <Link
        className="pf-c-button pf-m-plain"
        aria-label={i18n._(t`Close`)}
        title={i18n._(t`Close`)}
        to={linkTo}
        {...props}
      >
        <TimesIcon />
      </Link>
    );
  }
  return (
    <Button variant="plain" aria-label={i18n._(t`Close`)} {...props}>
      <TimesIcon />
    </Button>
  );
}
CardCloseButton.propTypes = {
  linkTo: string,
};
CardCloseButton.defaultProps = {
  linkTo: null,
};

export default withI18n()(CardCloseButton);
