// Base64 encoder/decoder with UTF-8 support
//
// Copyright (c) 2011 Vitaly Puzrin
// Copyright (c) 2011 Aleksey V Zapparov
//
// Author: Aleksey V Zapparov AKA ixti (http://www.ixti.net/)
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.


// Based on original artworks of base64 encoder/decoder by [Mozilla][1]
// [1]: http://lxr.mozilla.org/mozilla/source/extensions/xml-rpc/src/nsXmlRpcClient.js


(function (exports) {
  'use strict';

  var noop = function () {},
      logger = {warn: noop, error: noop},
      padding = '=',
      chrTable = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' +
                 '0123456789+/',
      binTable = [
        -1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,-1,
        -1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,-1,
        -1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,62, -1,-1,-1,63,
        52,53,54,55, 56,57,58,59, 60,61,-1,-1, -1, 0,-1,-1,
        -1, 0, 1, 2,  3, 4, 5, 6,  7, 8, 9,10, 11,12,13,14,
        15,16,17,18, 19,20,21,22, 23,24,25,-1, -1,-1,-1,-1,
        -1,26,27,28, 29,30,31,32, 33,34,35,36, 37,38,39,40,
        41,42,43,44, 45,46,47,48, 49,50,51,-1, -1,-1,-1,-1
      ];

  if (window.console) {
    logger = window.console;
    logger.warn = logger.warn || logger.error || logger.log || noop;
    logger.error = logger.error || logger.warn || logger.log || noop;
  }

  // internal helpers //////////////////////////////////////////////////////////

  function utf8Encode(str) {
    var bytes = [], offset = 0, length, char;

    str = encodeURI(str);
    length = str.length;

    while (offset < length) {
      char = str.charAt(offset);
      offset += 1;

      if ('%' !== char) {
        bytes.push(char.charCodeAt(0));
      } else {
        char = str.charAt(offset) + str.charAt(offset + 1);
        bytes.push(parseInt(char, 16));
        offset += 2;
      }
    }

    return bytes;
  }

  function utf8Decode(bytes) {
    var chars = [], offset = 0, length = bytes.length, c1, c2, c3;

    while (offset < length) {
      c1 = bytes[offset];
      c2 = bytes[offset + 1];
      c3 = bytes[offset + 2];

      if (128 > c1) {
        chars.push(String.fromCharCode(c1));
        offset += 1;
      } else if (191 < c1 && c1 < 224) {
        chars.push(String.fromCharCode(((c1 & 31) << 6) | (c2 & 63)));
        offset += 2;
      } else {
        chars.push(String.fromCharCode(((c1 & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63)));
        offset += 3;
      }
    }

    return chars.join('');
  }

  // public api ////////////////////////////////////////////////////////////////

  function encode(str) {
    var result = '',
        bytes = utf8Encode(str),
        length = bytes.length,
        i;

    // Convert every three bytes to 4 ascii characters.
    for (i = 0; i < (length - 2); i += 3) {
      result += chrTable[bytes[i] >> 2];
      result += chrTable[((bytes[i] & 0x03) << 4) + (bytes[i+1] >> 4)];
      result += chrTable[((bytes[i+1] & 0x0f) << 2) + (bytes[i+2] >> 6)];
      result += chrTable[bytes[i+2] & 0x3f];
    }

    // Convert the remaining 1 or 2 bytes, pad out to 4 characters.
    if (length%3) {
      i = length - (length%3);
      result += chrTable[bytes[i] >> 2];
      if ((length%3) === 2) {
        result += chrTable[((bytes[i] & 0x03) << 4) + (bytes[i+1] >> 4)];
        result += chrTable[(bytes[i+1] & 0x0f) << 2];
        result += padding;
      } else {
        result += chrTable[(bytes[i] & 0x03) << 4];
        result += padding + padding;
      }
    }

    return result;
  }

  function decode(data) {
    var value, code, idx = 0,
        bytes = [],
        leftbits = 0, // number of bits decoded, but yet to be appended
        leftdata = 0; // bits decoded, but yet to be appended

    // Convert one by one.
    for (idx = 0; idx < data.length; idx += 1) {
      code = data.charCodeAt(idx);
      value = binTable[code & 0x7F];

      if (-1 === value) {
        // Skip illegal characters and whitespace
        logger.warn("Illegal characters (code=" + code + ") in position " + idx);
      } else {
        // Collect data into leftdata, update bitcount
        leftdata = (leftdata << 6) | value;
        leftbits += 6;

        // If we have 8 or more bits, append 8 bits to the result
        if (leftbits >= 8) {
          leftbits -= 8;
          // Append if not padding.
          if (padding !== data.charAt(idx)) {
            bytes.push((leftdata >> leftbits) & 0xFF);
          }
          leftdata &= (1 << leftbits) - 1;
        }
      }
    }

    // If there are any bits left, the base64 string was corrupted
    if (leftbits) {
      logger.error("Corrupted base64 string");
      return null;
    }

    return utf8Decode(bytes);
  }

  exports.base64 = {encode: encode, decode: decode};
}(window));


////////////////////////////////////////////////////////////////////////////////
// vim:ts=2:sw=2
////////////////////////////////////////////////////////////////////////////////
