import atLibServices from '~services';

import actionGroup from '~components/action/action-group.directive';
import actionButton from '~components/action/action-button.directive';
import approvalsDrawer from '~components/approvalsDrawer/approvalsDrawer.directive';
import dialog from '~components/dialog/dialog.component';
import divider from '~components/utility/divider.directive';
import dynamicSelect from '~components/input/dynamic-select.directive';
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
import launchTemplate from '~components/launchTemplateButton/launchTemplateButton.component';
import layout from '~components/layout/layout.directive';
import list from '~components/list/list.directive';
import lookupList from '~components/lookup-list/lookup-list.component';
import modal from '~components/modal/modal.directive';
import panel from '~components/panel/panel.directive';
import panelBody from '~components/panel/body.directive';
import panelHeading from '~components/panel/heading.directive';
import popover from '~components/popover/popover.directive';
import relaunch from '~components/relaunchButton/relaunchButton.component';
import row from '~components/list/row.directive';
import rowItem from '~components/list/row-item.directive';
import rowAction from '~components/list/row-action.directive';
import sideNav from '~components/layout/side-nav.directive';
import sideNavItem from '~components/layout/side-nav-item.directive';
import tab from '~components/tabs/tab.directive';
import tabGroup from '~components/tabs/group.directive';
import tag from '~components/tag/tag.directive';
import toggleTag from '~components/toggle-tag/toggle-tag.directive';
import toolbar from '~components/list/list-toolbar.directive';
import topNavItem from '~components/layout/top-nav-item.directive';
import truncate from '~components/truncate/truncate.directive';
import atCodeMirror from '~components/code-mirror';
import atSyntaxHighlight from '~components/syntax-highlight';
import card from '~components/cards/card.directive';
import cardGroup from '~components/cards/group.directive';
import atSwitch from '~components/switch/switch.directive';

import BaseInputController from '~components/input/base.controller';
import ComponentsStrings from '~components/components.strings';

const MODULE_NAME = 'at.lib.components';

angular
    .module(MODULE_NAME, [
        atLibServices,
        atCodeMirror,
        atSyntaxHighlight,
    ])
    .directive('atActionGroup', actionGroup)
    .directive('atActionButton', actionButton)
    .directive('atApprovalsDrawer', approvalsDrawer)
    .component('atDialog', dialog)
    .directive('atDivider', divider)
    .directive('atDynamicSelect', dynamicSelect)
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
    .component('atLaunchTemplate', launchTemplate)
    .directive('atLayout', layout)
    .directive('atList', list)
    .component('atLookupList', lookupList)
    .directive('atListToolbar', toolbar)
    .component('atRelaunch', relaunch)
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
    .directive('atTag', tag)
    .directive('atToggleTag', toggleTag)
    .directive('atTopNavItem', topNavItem)
    .directive('atTruncate', truncate)
    .directive('atCard', card)
    .directive('atCardGroup', cardGroup)
    .directive('atSwitch', atSwitch)
    .service('BaseInputController', BaseInputController)
    .service('ComponentsStrings', ComponentsStrings);

export default MODULE_NAME;
