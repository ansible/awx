import React from 'react';
import {
  WizardFooter,
  WizardContextConsumer,
  Button,
} from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

const STEPS = {
  INVENTORY: 'inventory',
  CREDENTIALS: 'credentials',
  PASSWORDS: 'passwords',
  OTHER_PROMPTS: 'other',
  SURVEY: 'survey',
  PREVIEW: 'preview',
};

export function PromptFooter({ firstStep, i18n }) {
  return (
    <WizardFooter>
      <WizardContextConsumer>
        {({
          activeStep,
          goToStepByName,
          goToStepById,
          onNext,
          onBack,
          onClose,
        }) => {
          if (activeStep.name !== STEPS.PREVIEW) {
            return (
              <>
                <Button variant="primary" type="submit" onClick={onNext}>
                  {activeStep.nextButtonText || i18n._(t`Next`)}
                </Button>
                <Button
                  variant="secondary"
                  onClick={onBack}
                  className={activeStep.id === firstStep ? 'pf-m-disabled' : ''}
                >
                  {i18n._(t`Back`)}
                </Button>
                <Button variant="link" onClick={onClose}>
                  {i18n._(t`Cancel`)}
                </Button>
              </>
            );
          }
          return (
            <>
              <Button onClick={() => this.validateLastStep(onNext)}>
                {activeStep.nextButtonText || i18n._(t`Launch`)}
              </Button>
              <Button onClick={() => goToStepByName('Step 1')}>
                Go to Beginning
              </Button>
            </>
          );
        }}
      </WizardContextConsumer>
    </WizardFooter>
  );
}

export { PromptFooter as _PromptFooter };
export default withI18n()(PromptFooter);
