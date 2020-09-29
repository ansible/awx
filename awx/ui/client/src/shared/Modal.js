/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 *  @ngdoc function
 *  @name shared.function:Modal
 *  @description
 *  Modal.js
 *
 *  Create a draggable, resizable modal dialog using jQueryUI.
 *
 *
 */


export default
angular.module('ModalDialog', ['Utilities'])

    /**
     * @ngdoc method
     * @name shared.function:Modal#CreateDialog
     * @methodOf shared.function:Modal
     * @description
     * CreateDialog({
     *     id:          - id attribute value of the target DOM element
     *     scope:       - Required, $scope associated with the #id DOM element
     *     buttons:     - Required, Array of button objects. See example below.
     *     width:       - Desired width of modal dialog on open. Defaults to 500.
     *     height:      - Desired height of modal on open. Defaults to 600.
     *     minWidth:    - Minimum width that must be maintained regardless of reize attempts. Defaults to 400.
     *     title:       - Modal window title, optional
     *     onResizeStop: - Function to call when user stops resizing the dialog, optional
     *     onClose:      - Function to call after window closes, optional
     *     onOpen:       - Function to call after window opens, optional
     *     beforeDestroy: - Function to call during onClose and prior to destroying the window
     *     callback:     - String to pass to scope.$emit() after dialog is created, optional
     * })
     *
     * Note that the dialog will be created but not opened. It's up to the caller to open it. Use callback
     * option to respond to dialog created event.
     */
    .factory('CreateDialog', ['Empty', function(Empty) {

        return function(params) {

            let scope = params.scope,
                buttonSet = params.buttons,
                width = params.width || 500,
                height = params.height || 600,
                minWidth = params.minWidth || 300,
                title = params.title || '',
                onResizeStop = params.onResizeStop,
                onClose = params.onClose,
                onOpen = params.onOpen,
                _allowInteraction = params._allowInteraction,
                callback = params.callback,
                beforeDestroy = params.beforeDestroy,
                closeOnEscape = (params.closeOnEscape === undefined) ? false : params.closeOnEscape,
                resizable = (params.resizable === undefined) ? false : params.resizable,
                draggable = (params.draggable === undefined) ? true : params.draggable,
                dialogClass = params.dialogClass,
                forms = _.chain([params.form]).flatten().compact().value(),
                buttons,
                id = params.id,
                position = (params.position === undefined) ? { my: "center", at: "center", of: window } : params.position,
                x, y, wh, ww;

            function updateButtonStatus(isValid) {
                $('.ui-dialog[aria-describedby="' + id + '"]').find('.btn-primary').prop('disabled', !isValid);
            }

            if (Empty(buttonSet)) {
                // Default button object
                buttonSet = [{
                    label: "OK",
                    onClick: function() {
                        scope.modalOK();
                    },
                    icon: "",
                    "class": "btn btn-primary",
                    "id": "dialog-ok-button"
                }];
            }

            buttons = {};
            buttonSet.forEach( function(btn) {
                buttons[btn.label] = btn.onClick;
            });

            // Set modal dimensions based on viewport width
            ww = $(document).width();
            wh = $(document).height();
            x = (width > ww) ? ww - 10 : width;
            y = height === "auto" ? "auto" : ((height > wh) ? wh - 10 : height);

            // Create the modal
            $('#' + id).dialog({
                buttons: buttons,
                modal: true,
                width: x,
                height: y,
                autoOpen: false,
                minWidth: minWidth,
                title: title,
                closeOnEscape: closeOnEscape,
                resizable: resizable,
                draggable: draggable,
                dialogClass: dialogClass,
                position: position,
                create: function () {
                    // Fix the close button
                    $('.ui-dialog[aria-describedby="' + id + '"]').find('.ui-dialog-titlebar button').empty().attr({'class': 'close'}).html('<i class="fa fa-times-circle"></i>');

                    setTimeout(function() {
                        // Make buttons bootstrapy
                        $('.ui-dialog[aria-describedby="' + id + '"]').find('.ui-dialog-buttonset button').each(function () {
                            var txt = $(this).text(), self = $(this);
                            buttonSet.forEach(function(btn) {
                                if (txt === btn.label) {
                                    self.attr({ "class": btn['class'], "id": btn.id });
                                    if (btn.icon) {
                                        self.empty().html('<i class="fa ' + btn.icon + '"></i> ' + btn.label);
                                    }
                                }
                            });
                        });
                    }, 300);

                    if (forms.length > 0) {
                        forms.map(function(form_ctrl) {
                            scope.$watch(form_ctrl.$name + '.$valid', updateButtonStatus);
                        });
                    }

                    setTimeout(function() {
                        scope.$apply(function() {
                            scope.$emit(callback);
                        });
                    }, 300);
                },
                resizeStop: function () {
                    // for some reason, after resizing dialog the form and fields (the content) doesn't expand to 100%
                    var dialog = $('.ui-dialog[aria-describedby="' + id + '"]'),
                        titleHeight = dialog.find('.ui-dialog-titlebar').outerHeight(),
                        buttonHeight = dialog.find('.ui-dialog-buttonpane').outerHeight(),
                        content = dialog.find('#' + id);
                    content.width(dialog.width() - 28);
                    content.css({ height: (dialog.height() - titleHeight - buttonHeight - 10) });
                    if (onResizeStop) {
                        onResizeStop();
                    }
                },
                close: function () {
                    // Destroy on close
                    $('.tooltip').each(function () {
                        // Remove any lingering tooltip <div> elements
                        $(this).remove();
                    });
                    $('.popover').each(function () {
                        // remove lingering popover <div> elements
                        $(this).remove();
                    });
                    if (beforeDestroy) {
                        beforeDestroy();
                    }
                    $('#' + id).dialog('destroy');
                    $('#' + id).hide();
                    if (onClose) {
                        onClose();
                    }
                },
                open: function () {
                    $('.tooltip').each(function () {
                        // Remove any lingering tooltip <div> elements
                        $(this).remove();
                    });
                    $('.popover').each(function () {
                        // remove lingering popover <div> elements
                        $(this).remove();
                    });
                    if (onOpen) {
                        onOpen();
                    }
                },
                _allowInteraction: _allowInteraction
            });
        };
    }])

    /**
     * TextareaResize({
     *     scope:           - $scope associated with the textarea element
     *     textareaId:      - id attribute value of the textarea
     *     modalId:         - id attribute of the <div> element used to create the modal
     *     formId:          - id attribute of the textarea's parent form
     *     parse:           - if true, call ParseTypeChange and replace textarea with codemirror editor
     *     fld:             - optional, form field name
     *     bottom_margin:   - optional, integer value for additional margin to leave below the textarea
     *     onChange;        - optional, function to call when the textarea value changes
     *  })
     *
     *  Use to resize a textarea field contained on a modal. Has only been tested where the
     *  form contains 1 textarea and the textarea is at the bottom of the form/modal.
     *
     **/
    .factory('TextareaResize', ['ParseTypeChange', 'Wait', function(ParseTypeChange, Wait){
        return function(params) {

            var scope = params.scope,
                textareaId = params.textareaId,
                modalId = params.modalId,
                formId = params.formId,
                fld = params.fld,
                parse = (params.parse === undefined) ? true : params.parse,
                bottom_margin = (params.bottom_margin) ? params.bottom_margin : 0,
                onChange = params.onChange,
                textarea,
                formHeight, model, windowHeight, offset, rows;

            function waitStop() {
                Wait('stop');
            }

            // Attempt to create the largest textarea field that will fit on the window. Minimum
            // height is 6 rows, so on short windows you will see vertical scrolling
            textarea = $('#' + textareaId);
            if (scope.codeMirror) {
                model = textarea.attr('ng-model');
                scope[model] = scope.codeMirror.getValue();
                scope.codeMirror.destroy();
            }
            textarea.attr('rows', 1);
            formHeight = $('#' + formId).height();
            windowHeight = $('#' + modalId).height() - 20;   //leave a margin of 20px
            offset = Math.floor(windowHeight - formHeight - bottom_margin);
            rows = Math.floor(offset / 20);
            rows = (rows < 6) ? 6 : rows;
            textarea.attr('rows', rows);
            while(rows > 6 && ($('#' + formId).height() > $('#' + modalId).height() + bottom_margin)) {
                rows--;
                textarea.attr('rows', rows);
            }
            if (parse) {
                ParseTypeChange({ scope: scope, field_id: textareaId, onReady: waitStop, variable: fld, onChange: onChange });
            }
        };
    }]);
