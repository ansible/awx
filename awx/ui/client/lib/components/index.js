import atLibServices from '~services';

import actionGroup from '~components/action/action-group.directive';
import divider from '~components/utility/divider.directive';
import form from '~components/form/form.directive';
import formAction from '~components/form/action.directive';
import inputCheckbox from '~components/input/checkbox.directive';
import inputFile from '~components/input/file.directive';
import inputGroup from '~components/input/group.directive';
import inputLabel from '~components/input/label.directive';
import inputLookup from '~components/input/lookup.directive';
import inputMessage from '~components/input/message.directive';
import inputSecret from '~components/input/secret.directive';
import inputSelect from '~components/input/select.directive';
import inputSlider from '~components/input/slider.directive';
import inputText from '~components/input/text.directive';
import inputTextarea from '~components/input/textarea.directive';
import inputTextareaSecret from '~components/input/textarea-secret.directive';
import layout from '~components/layout/layout.directive';
import list from '~components/list/list.directive';
import row from '~components/list/row.directive';
import rowItem from '~components/list/row-item.directive';
import rowAction from '~components/list/row-action.directive';
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
import relaunch from '~components/relaunchButton/relaunchButton.component';

import BaseInputController from '~components/input/base.controller';
import ComponentsStrings from '~components/components.strings';
import conditionalAttributes from '~components/utility/conditional-attributes.directive';

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
    .directive('atInputFile', inputFile)
    .directive('atInputGroup', inputGroup)
    .directive('atInputLabel', inputLabel)
    .directive('atInputLookup', inputLookup)
    .directive('atInputMessage', inputMessage)
    .directive('atInputSecret', inputSecret)
    .directive('atInputSelect', inputSelect)
    .directive('atInputSlider', inputSlider)
    .directive('atInputText', inputText)
    .directive('atInputTextarea', inputTextarea)
    .directive('atInputTextareaSecret', inputTextareaSecret)
    .directive('atLayout', layout)
    .directive('atList', list)
    .directive('atRow', row)
    .directive('atRowItem', rowItem)
    .directive('atRowAction', rowAction)
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
    .component('atRelaunch', relaunch)
    .directive('conditionalAttributes', conditionalAttributes)
    .service('BaseInputController', BaseInputController)
    .service('ComponentsStrings', ComponentsStrings);

export default MODULE_NAME;
