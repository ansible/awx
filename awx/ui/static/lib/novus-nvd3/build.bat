@echo off
copy src\intro.js /B + src\core.js /B + src\tooltip.js /B temp1.js /B
copy src\models\*.js /B temp2.js /B
copy temp1.js /B + temp2.js /B + src\outro.js /B nv.d3.js /B
del temp1.js
del temp2.js
