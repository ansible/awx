import React from 'react';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { PasswordField } from '@components/FormField';
import { Formik } from 'formik';

import {
  Chip,
  Form,
  FormGroup,
  Modal,
  TextInput,
  TextArea,
  Select,
  SelectVariant,
} from '@patternfly/react-core';

// const Chip = styled(_Chip)`
//   margin-right: 5px;
// `;
function SurveyPreviewModal({
  questions,
  isPreviewModalOpen,
  onToggleModalOpen,
  i18n,
}) {
  const initialValues = {};
  questions.forEach(q => {
    initialValues[q.variable] = q.default;
    return initialValues;
  });

  return (
    <Modal
      title={i18n._(t`Survey Preview`)}
      isOpen={isPreviewModalOpen}
      onClose={() => onToggleModalOpen(false)}
      isSmall
    >
      <Formik initialValues={initialValues}>
        {() => (
          <Form>
            {questions.map(q => (
              <div key={q.variable}>
                {['text', 'integer', 'float'].includes(q.type) && (
                  <FormGroup
                    fieldId={`survey-preview-text-${q.variable}`}
                    label={q.question_name}
                  >
                    <TextInput
                      id={`survey-preview-text-${q.variable}`}
                      value={q.default}
                      isDisabled
                      aria-label={i18n._(t`Text`)}
                    />
                  </FormGroup>
                )}
                {['textarea'].includes(q.type) && (
                  <FormGroup
                    fieldId={`survey-preview-textArea-${q.variable}`}
                    label={q.question_name}
                  >
                    <TextArea
                      id={`survey-preview-textArea-${q.variable}`}
                      type={`survey-preview-textArea-${q.variable}`}
                      value={q.default}
                      aria-label={i18n._(t`Text Area`)}
                      disabled
                    />
                  </FormGroup>
                )}
                {['password'].includes(q.type) && (
                  <PasswordField
                    id={`survey-preview-password-${q.variable}`}
                    label={q.question_name}
                    name={q.variable}
                    isDisabled
                  />
                )}
                {['multiplechoice'].includes(q.type) && (
                  <FormGroup
                    fieldId={`survey-preview-multipleChoice-${q.variable}`}
                    label={q.question_name}
                  >
                    <Select
                      id={`survey-preview-multipleChoice-${q.variable}`}
                      isDisabled
                      aria-label={i18n._(t`Multiple Choice`)}
                      placeholderText={q.default}
                      onToggle={() => {}}
                    />
                  </FormGroup>
                )}
                {['multiselect'].includes(q.type) && (
                  <FormGroup
                    fieldId={`survey-preview-multiSelect-${q.variable}`}
                    label={q.question_name}
                  >
                    <Select
                      isDisabled
                      isReadOnly
                      variant={SelectVariant.typeaheadMulti}
                      isExpanded={false}
                      selections={q.default.length > 0 && q.default.split('\n')}
                      onToggle={() => {}}
                      aria-label={i18n._(t`Multi-Select`)}
                      id={`survey-preview-multiSelect-${q.variable}`}
                    />
                  </FormGroup>
                )}
              </div>
            ))}
          </Form>
        )}
      </Formik>
    </Modal>
  );
}
export default withI18n()(SurveyPreviewModal);
