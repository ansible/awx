/*
**    Created by: Jeff Todnem (http://www.todnem.com/)
**    Created on: 2007-08-14
**    Last modified: 2013-07-31 by James Cammarata
**
**    License Information:
**    -------------------------------------------------------------------------
**    Copyright (C) 2007 Jeff Todnem
**
**    This program is free software; you can redistribute it and/or modify it
**    under the terms of the GNU General Public License as published by the
**    Free Software Foundation; either version 2 of the License, or (at your
**    option) any later version.
**    
**    This program is distributed in the hope that it will be useful, but
**    WITHOUT ANY WARRANTY; without even the implied warranty of
**    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
**    General Public License for more details.
**    
**    You should have received a copy of the GNU General Public License along
**    with this program; if not, write to the Free Software Foundation, Inc.,
**    59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
**    
*/

/*
function addLoadEvent(func) {
   var oldonload = window.onload;
   if (typeof window.onload != "function") {
      window.onload = func;
   }
   else {
      window.onload = function() {
         if (oldonload) {
            oldonload();
         }
         func();
      };
   }
}

function $() {
   var arrElms = [];
   for (var i=0; i < arguments.length; i++) {
      var elm = arguments[i];
      if (typeof(elm == "string")) { elm = document.getElementById(elm); }
      if (arguments.length == 1) { return elm; }
      arrElms.push(elm);
   }
   return arrElms;
}
*/

String.prototype.strReverse = function() {
   var newstring = "";
   for (var s=0; s < this.length; s++) {
      newstring = this.charAt(s) + newstring;
   }
   return newstring;
   //strOrig = ' texttotrim ';
   //strReversed = strOrig.revstring();
};

var nScore = 0;
function chkPass(pwd) {
   // Simultaneous variable declaration and value assignment aren't supported in IE apparently
   // so I'm forced to assign the same value individually per var to support a crappy browser *sigh* 
   var nLength=0, nAlphaUC=0, nAlphaLC=0, nNumber=0, nSymbol=0, nMidChar=0, nRequirements=0, 
       nAlphasOnly=0, nNumbersOnly=0, nUnqChar=0, nRepChar=0, nRepInc=0, nConsecAlphaUC=0, nConsecAlphaLC=0, 
       nConsecNumber=0, nConsecSymbol=0, nConsecCharType=0, nSeqAlpha=0, nSeqNumber=0, nSeqSymbol=0, 
       nSeqChar=0, nReqChar=0, nMultConsecCharType=0;
   var nMultRepChar=1, nMultConsecSymbol=1;
   var nMultMidChar=2, nMultRequirements=2, nMultConsecAlphaUC=2, nMultConsecAlphaLC=2, nMultConsecNumber=2;
   var nReqCharType=3, nMultAlphaUC=3, nMultAlphaLC=3, nMultSeqAlpha=3, nMultSeqNumber=3, nMultSeqSymbol=3;
   var nMultLength=4, nMultNumber=4;
   var nMultSymbol=6;
   var nTmpAlphaUC="", nTmpAlphaLC="", nTmpNumber="", nTmpSymbol="";
   var sAlphaUC="0", sAlphaLC="0", sNumber="0", sSymbol="0", sMidChar="0", sRequirements="0", 
       sAlphasOnly="0", sNumbersOnly="0", sRepChar="0", sConsecAlphaUC="0", sConsecAlphaLC="0", 
       sConsecNumber="0", sSeqAlpha="0", sSeqNumber="0", sSeqSymbol="0";
   var sAlphas = "abcdefghijklmnopqrstuvwxyz";
   var sNumerics = "01234567890";
   var sSymbols = ")!@#$%^&*()";
   var sComplexity = "Too Short";
   var sStandards = "Below";
   var nMinPwdLen = 8;
   if (document.all) { var nd = 0; } else { var nd = 1; }
   if (pwd) {
      nScore = parseInt(pwd.length * nMultLength);
      nLength = pwd.length;
      var arrPwd = pwd.replace(/\s+/g,"").split(/\s*/);
      var arrPwdLen = arrPwd.length;
      
      /* Loop through password to check for Symbol, Numeric, Lowercase and Uppercase pattern matches */
      for (var a=0; a < arrPwdLen; a++) {
         if (arrPwd[a].match(/[A-Z]/g)) {
            if (nTmpAlphaUC !== "") { if ((nTmpAlphaUC + 1) == a) { nConsecAlphaUC++; nConsecCharType++; } }
            nTmpAlphaUC = a;
            nAlphaUC++;
         }
         else if (arrPwd[a].match(/[a-z]/g)) { 
            if (nTmpAlphaLC !== "") { if ((nTmpAlphaLC + 1) == a) { nConsecAlphaLC++; nConsecCharType++; } }
            nTmpAlphaLC = a;
            nAlphaLC++;
         }
         else if (arrPwd[a].match(/[0-9]/g)) { 
            if (a > 0 && a < (arrPwdLen - 1)) { nMidChar++; }
            if (nTmpNumber !== "") { if ((nTmpNumber + 1) == a) { nConsecNumber++; nConsecCharType++; } }
            nTmpNumber = a;
            nNumber++;
         }
         else if (arrPwd[a].match(/[^a-zA-Z0-9_]/g)) { 
            if (a > 0 && a < (arrPwdLen - 1)) { nMidChar++; }
            if (nTmpSymbol !== "") { if ((nTmpSymbol + 1) == a) { nConsecSymbol++; nConsecCharType++; } }
            nTmpSymbol = a;
            nSymbol++;
         }
         /* Internal loop through password to check for repeat characters */
         var bCharExists = false;
         for (var b=0; b < arrPwdLen; b++) {
            if (arrPwd[a] == arrPwd[b] && a != b) { /* repeat character exists */
               bCharExists = true;
               /* 
               Calculate icrement deduction based on proximity to identical characters
               Deduction is incremented each time a new match is discovered
               Deduction amount is based on total password length divided by the
               difference of distance between currently selected match
               */
               nRepInc += Math.abs(arrPwdLen/(b-a));
            }
         }
         if (bCharExists) { 
            nRepChar++; 
            nUnqChar = arrPwdLen-nRepChar;
            nRepInc = (nUnqChar) ? Math.ceil(nRepInc/nUnqChar) : Math.ceil(nRepInc); 
         }
      }
      
      /* Check for sequential alpha string patterns (forward and reverse) */
      for (var s=0; s < 23; s++) {
         var sFwd = sAlphas.substring(s,parseInt(s+3));
         var sRev = sFwd.strReverse();
         if (pwd.toLowerCase().indexOf(sFwd) != -1 || pwd.toLowerCase().indexOf(sRev) != -1) { nSeqAlpha++; nSeqChar++;}
      }
      
      /* Check for sequential numeric string patterns (forward and reverse) */
      for (var s=0; s < 8; s++) {
         var sFwd = sNumerics.substring(s,parseInt(s+3));
         var sRev = sFwd.strReverse();
         if (pwd.toLowerCase().indexOf(sFwd) != -1 || pwd.toLowerCase().indexOf(sRev) != -1) { nSeqNumber++; nSeqChar++;}
      }
      
      /* Check for sequential symbol string patterns (forward and reverse) */
      for (var s=0; s < 8; s++) {
         var sFwd = sSymbols.substring(s,parseInt(s+3));
         var sRev = sFwd.strReverse();
         if (pwd.toLowerCase().indexOf(sFwd) != -1 || pwd.toLowerCase().indexOf(sRev) != -1) { nSeqSymbol++; nSeqChar++;}
      }
      
      /* Modify overall score value based on usage vs requirements */

      /* General point assignment */
      if (nAlphaUC > 0 && nAlphaUC < nLength) {   
         nScore = parseInt(nScore + ((nLength - nAlphaUC) * 2));
         sAlphaUC = "+ " + parseInt((nLength - nAlphaUC) * 2); 
      }
      if (nAlphaLC > 0 && nAlphaLC < nLength) {   
         nScore = parseInt(nScore + ((nLength - nAlphaLC) * 2)); 
         sAlphaLC = "+ " + parseInt((nLength - nAlphaLC) * 2);
      }
      if (nNumber > 0 && nNumber < nLength) {   
         nScore = parseInt(nScore + (nNumber * nMultNumber));
         sNumber = "+ " + parseInt(nNumber * nMultNumber);
      }
      if (nSymbol > 0) {   
         nScore = parseInt(nScore + (nSymbol * nMultSymbol));
         sSymbol = "+ " + parseInt(nSymbol * nMultSymbol);
      }
      if (nMidChar > 0) {   
         nScore = parseInt(nScore + (nMidChar * nMultMidChar));
         sMidChar = "+ " + parseInt(nMidChar * nMultMidChar);
      }

      /* Point deductions for poor practices */
      if ((nAlphaLC > 0 || nAlphaUC > 0) && nSymbol === 0 && nNumber === 0) {  // Only Letters
         nScore = parseInt(nScore - nLength);
         nAlphasOnly = nLength;
         sAlphasOnly = "- " + nLength;
      }
      if (nAlphaLC === 0 && nAlphaUC === 0 && nSymbol === 0 && nNumber > 0) {  // Only Numbers
         nScore = parseInt(nScore - nLength); 
         nNumbersOnly = nLength;
         sNumbersOnly = "- " + nLength;
      }
      if (nRepChar > 0) {  // Same character exists more than once
         nScore = parseInt(nScore - nRepInc);
         sRepChar = "- " + nRepInc;
      }
      if (nConsecAlphaUC > 0) {  // Consecutive Uppercase Letters exist
         nScore = parseInt(nScore - (nConsecAlphaUC * nMultConsecAlphaUC)); 
         sConsecAlphaUC = "- " + parseInt(nConsecAlphaUC * nMultConsecAlphaUC);
      }
      if (nConsecAlphaLC > 0) {  // Consecutive Lowercase Letters exist
         nScore = parseInt(nScore - (nConsecAlphaLC * nMultConsecAlphaLC)); 
         sConsecAlphaLC = "- " + parseInt(nConsecAlphaLC * nMultConsecAlphaLC);
      }
      if (nConsecNumber > 0) {  // Consecutive Numbers exist
         nScore = parseInt(nScore - (nConsecNumber * nMultConsecNumber));  
         sConsecNumber = "- " + parseInt(nConsecNumber * nMultConsecNumber);
      }
      if (nSeqAlpha > 0) {  // Sequential alpha strings exist (3 characters or more)
         nScore = parseInt(nScore - (nSeqAlpha * nMultSeqAlpha)); 
         sSeqAlpha = "- " + parseInt(nSeqAlpha * nMultSeqAlpha);
      }
      if (nSeqNumber > 0) {  // Sequential numeric strings exist (3 characters or more)
         nScore = parseInt(nScore - (nSeqNumber * nMultSeqNumber)); 
         sSeqNumber = "- " + parseInt(nSeqNumber * nMultSeqNumber);
      }
      if (nSeqSymbol > 0) {  // Sequential symbol strings exist (3 characters or more)
         nScore = parseInt(nScore - (nSeqSymbol * nMultSeqSymbol)); 
         sSeqSymbol = "- " + parseInt(nSeqSymbol * nMultSeqSymbol);
      }

      /* Determine complexity based on overall score */
      if (nScore > 100) { nScore = 100; } else if (nScore < 0) { nScore = 0; }

      var progbar  = $("#progbar");
      progbar.css("width", nScore + '%');

      if (nScore >= 0 && nScore <= 33) {
         sComplexity = 'Weak';
         progbar.addClass('progress-bar-danger')
         progbar.removeClass('progress-bar-success progress-bar-warning')
      } else if (nScore > 33 && nScore <= 67) {
         sComplexity = 'Good';
         progbar.addClass('progress-bar-warning')
         progbar.removeClass('progress-bar-success progress-bar-danger')
      } else if (nScore > 67) {
         sComplexity = "Strong";
         progbar.addClass('progress-bar-success')
         progbar.removeClass('progress-bar-warning progress-bar-danger')
      }
   }
   else {
      /* no password, so reset the displays */
      var progbar  = $("#progbar");
      progbar.css("width", '0%');
      progbar.removeClass('progress-bar-success progress-bar-warning progress-bar-danger')
   }
   return nScore;
}