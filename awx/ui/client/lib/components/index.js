import atLibServices from '~services';

import actionGroup from '~components/action/action-group.directive';
import divider from '~components/utility/divider.directive';
import form from '~components/form/form.directive';
import formAction from '~components/form/action.directive';
import inputCheckbox from '~components/input/checkbox.directive';
import inputGroup from '~components/input/group.directive';
import inputLabel from '~components/input/label.directive';
import inputLookup from '~components/input/lookup.directive';
import inputMessage from '~components/input/message.directive';
import inputSecret from '~components/input/secret.directive';
import inputSelect from '~components/input/select.directive';
import inputText from '~components/input/text.directive';
import inputTextarea from '~components/input/textarea.directive';
import inputTextareaSecret from '~components/input/textarea-secret.directive';
import layout from '~components/layout/layout.directive';
import modal from '~components/modal/modal.directive';
import panel from '~components/panel/panel.directive';
import panelBody from '~components/panel/body.directive';
import panelHeading from '~components/panel/heading.directive';
import popover from '~components/popover/popover.directive';
import sideNav from '~components/layout/side-nav.directive';
import sideNavItem from '~components/layout/side-nav-item.directive';
import tab from '~components/tabs/tab.directive';
import tabGroup from '~components/tabs/group.directive';
import topNavItem from '~components/layout/top-nav-item.directive';
import truncate from '~components/truncate/truncate.directive';

import BaseInputController from '~components/input/base.controller';
import ComponentsStrings from '~components/components.strings';

const MODULE_NAME = 'at.lib.components';

angular
    .module(MODULE_NAME, [
        atLibServices
    ])
    .directive('atActionGroup', actionGroup)
    .directive('atDivider', divider)
    .directive('atForm', form)
    .directive('atFormAction', formAction)
    .directive('atInputCheckbox', inputCheckbox)
    .directive('atInputGroup', inputGroup)
    .directive('atInputLabel', inputLabel)
    .directive('atInputLookup', inputLookup)
    .directive('atInputMessage', inputMessage)
    .directive('atInputSecret', inputSecret)
    .directive('atInputSelect', inputSelect)
    .directive('atInputText', inputText)
    .directive('atInputTextarea', inputTextarea)
    .directive('atInputTextareaSecret', inputTextareaSecret)
    .directive('atLayout', layout)
    .directive('atModal', modal)
    .directive('atPanel', panel)
    .directive('atPanelBody', panelBody)
    .directive('atPanelHeading', panelHeading)
    .directive('atPopover', popover)
    .directive('atSideNav', sideNav)
    .directive('atSideNavItem', sideNavItem)
    .directive('atTab', tab)
    .directive('atTabGroup', tabGroup)
    .directive('atTopNavItem', topNavItem)
    .directive('atTruncate', truncate)
    .service('BaseInputController', BaseInputController)
    .service('ComponentsStrings', ComponentsStrings);

export default MODULE_NAME;
