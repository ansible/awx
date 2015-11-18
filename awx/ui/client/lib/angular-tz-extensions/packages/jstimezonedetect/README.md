## Introduction

This script gives you the zone info key representing your device's time zone setting. 

The return value is an [IANA zone info key][1] (aka the Olson time zone database).

The IANA timezone database is pretty much standard for most platforms (UNIX and Mac support it natively, and every programming language in the world either has native support or well maintained libraries that support it).

## Example Use

Since version 1.0.4 the [library is hosted on cdnjs.com][10]. I strongly recommend including it from there.

Invoke the script by calling

    :::javascript
        var tz = jstz.determine(); // Determines the time zone of the browser client
        tz.name(); // Returns the name of the time zone eg "Europe/Berlin"

## Use Case

The script is useful if you do not want to disturb your users with questions about what time zone they are in. You can rely on this script to give you a key that is usable for server side datetime normalisations across time zones. 

## Limitations

This script does not do geo-location, nor does it care very much about historical time zones. 

So if you are unhappy with the time zone "Europe/Berlin" when the user is in fact in "Europe/Stockholm" - this script is not for you. (They are both identical in modern time).

Also, if it is important to you to know that in Europe/Simferopool (Ukraine) the UTC offset before 1924 was +2.67, sorry, this script will not help you.

Time zones are a screwed up thing, generally speaking, and the scope of this script is to solve problems concerning modern time zones, in this case from 2010 and forward.

## Demo

There is an updated demo running on: [http://pellepim.bitbucket.org/jstz/][2].

## Contribute?

If you want to contribute to the project (perhaps fix a bug, or reflect a change in time zone rules), please simply issue a Pull Request. Don't worry about [Grunt][4] builds etc, all you need to modify is the jstz.js file and I'll take care of the testing/minifying etc.

## Credits

Thanks to
  
  - [Josh Fraser][5] for the original idea
  - [Brian Donovan][6] for making jstz CommonJS compliant
  - [Ilya Sedlovsky][7] for help with namespacing
  - [Jordan Magnuson][9] for adding to cdnjs, documentation tags, and for reporting important issues

Other contributors:
[Gilmore Davidson][8]

[1]: http://www.iana.org/time-zones
[2]: http://pellepim.bitbucket.org/jstz/
[3]: https://bitbucket.org/pellepim/jstimezonedetect/src
[4]: https://github.com/gruntjs/grunt
[5]: http://www.onlineaspect.com/about/
[6]: https://bitbucket.org/eventualbuddha
[7]: https://bitbucket.org/purebill
[8]: https://bitbucket.org/gdavidson
[9]: https://github.com/JordanMagnuson
[10]: http://cdnjs.com
