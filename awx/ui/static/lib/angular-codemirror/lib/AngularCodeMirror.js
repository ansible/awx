/**********************************************
 * AngularCodeMirror.js
 *
 * Copyright (c) 2014 Chris Houseknecht
 *
 * The MIT License (MIT)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of angular-codemirror and associated files and documentation (the "Software"),
 * to deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

'use strict';

angular.module('AngularCodeMirrorModule', [])

    .factory('AngularCodeMirror', [ function() {
        return function() {
            var fn = function() {

                this.myCodeMirror = null;
                this.element = null;

                this.showTextArea = function(params) {
                    var self = this,
                        element = (typeof params.element === "object") ? params.element : document.getElementById(params.element),
                        scope = params.scope,
                        model = params.model,
                        mode = params.mode,
                        onReady = params.onReady,
                        onChange = params.onChange,
                        height = 0;

                    self.element = $(element);
                    
                    // We don't want to touch the original textarea. Angular likely has a model and other listeners
                    // attached to it. In prior iterations attaching CodeMirror to it seemed to go bad, so we'll insert a 
                    // <div> under it, hide the textarea and let CodeMirror attach to the <div>.
                    if ($('#cm-' + model + '-container').length > 0) {
                        $('#cm-' + model + '-container').empty();
                    }
                    else {
                        self.element.after("<div id=\"cm-" + model + "-container\"></div>");
                    }
                    
                    // Calc the height of the text area- our CodeMirror should match.
                    height += self.element.attr('rows') * parseInt($(self.element).css('line-height').replace(/px/,''),10);
                    height += parseInt(self.element.css('padding-top').replace(/px|%/,''),10) +
                        parseInt(self.element.css('padding-bottom').replace(/px|%/,''),10);
                    height += 2;  //for the border
                    
                    // hide
                    self.element.hide();

                    // Initialize CodeMirror
                    self.modes[mode].value = scope[model];
                    self.myCodeMirror = CodeMirror(document.getElementById('cm-' + model + '-container'), self.modes[mode]);

                    // Adjust the height
                    $('.CodeMirror').css({ 'min-height': height, 'max-height': height });
                    self.myCodeMirror.setSize(null, height);

                    // This doesn't work without a setTimeout
                    setTimeout(function() {
                        self.myCodeMirror.refresh();
                        if (onReady) {
                            onReady();
                        }
                    }, 500);

                    // Update the model on change
                    self.myCodeMirror.on('change', function() {
                        setTimeout(function() {
                            scope.$apply(function(){
                                scope[model] = self.myCodeMirror.getValue();
                                if (onChange) {
                                    onChange();
                                }
                            });
                        }, 500);
                    });
                };
               
                this.getValue = function() {
                    var self = this;
                    return self.myCodeMirror.getValue();
                };

                this.destroy = function() {
                    // Intended for use with showTextArea. This will get ride of CM and put the
                    // textarea back to normal
                    var self = this;
                    $('.CodeMirror').empty().remove();
                    if (self.element) {
                        self.element.show();
                    }
                };

                this.showModal = function(params) {
                    
                    var self = this,
                        scope = params.scope,
                        target = (typeof params.container === "string") ? document.getElementById(params.container) : params.container,
                        mode = params.mode,
                        model = params.model,
                        title = params.title || 'Code Editor',
                        modes = self.modes;

                    this.html = "<div id=\"af-code-editor-modal\"><div id=\"af-code\"></div>\n</div>\n";
                    if ($('#af-code-editor-modal').length === 0) {
                        $(target).append(this.html);
                    }
                    else {
                        $('#af-code-editor-modal').remove();
                        $(target).append(this.html);
                    }

                    $('#af-code-editor-modal').dialog({
                        title: title,
                        resizable: true,
                        width: Math.ceil($(window).width() * 0.9),
                        height: Math.ceil($(window).height() * 0.8),
                        position: "center",
                        show: true,
                        closeOnEscape: true,
                        modal: true,
                        autoOpen: true,
                        buttons: [
                            { text: "Cancel", id: "af-code-edit-cancel", click: function() { $(this).dialog('close'); } },
                            { text: "OK", id: "af-code-edit-ok", click:
                                function() {
                                    scope.$apply(function() { scope[model] = self.myCodeMirror.getValue(); });
                                    $(this).dialog('close');
                                }
                            }
                        ],
                        open: function() {
                            var self = $('.ui-dialog[aria-describedby="af-code-editor-modal"]'),
                                idx, options;
                            
                            // bring the overlay up to just below the new window
                            idx = self.css('z-index');
                            $('.ui-widget-overlay').css({ 'z-index': idx - 1});
                            
                            // fix buttons- make them more twittery
                            self.find('.ui-dialog-titlebar button').empty().attr({'class': 'close'}).text('x');
                            $('#af-code-edit-cancel').attr({ "class": "btn btn-default" }).empty().html("<i class=\"fa fa-times\"></i> Cancel");
                            $('#af-code-edit-ok').attr({ "class": "btn btn-primary" }).empty().html("<i class=\"fa fa-check\"></i> Save");

                            // initialize CodeMirror
                            options = modes[mode];
                            options.value = scope[model];
                            self.myCodeMirror = CodeMirror(document.getElementById('af-code'), options);
                        }
                    });
                };

                // Don't maintain modes here. Use this.addModes() to set/override available modes
                this.modes = {};
                
                // Add or override available modes.
                this.addModes = function(obj) {
                    for (var key in obj) {
                        if (this.modes[key]) {
                            delete this.modes[key];
                        }
                        this.modes[key] = angular.copy(obj[key]);
                    }
                };
            };
            return new fn();
        };
    }]);
