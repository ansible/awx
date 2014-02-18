#!/bin/bash

#
# Minify angular-forms.js
#
# ./compile.sh
#

if [ -f ../angular-forms.min.js ]; then
   rm ../angular-forms.min.js
fi
java -jar ../bower_components/closure-compiler/compiler.jar --js ../angular-forms.js --js_output_file ../angular-forms.min.js
