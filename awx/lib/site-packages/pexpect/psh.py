'''This is a utility class to make shell scripting easier in Python.
It combines Pexpect and wraps many Standard Python Library functions
to make them look more shell-like.

This module is undocumented, so its API is provisional, and may change in
future releases without a deprecation cycle.

PEXPECT LICENSE

    This license is approved by the OSI and FSF as GPL-compatible.
        http://opensource.org/licenses/isc-license.txt

    Copyright (c) 2012, Noah Spurrier <noah@noah.org>
    PERMISSION TO USE, COPY, MODIFY, AND/OR DISTRIBUTE THIS SOFTWARE FOR ANY
    PURPOSE WITH OR WITHOUT FEE IS HEREBY GRANTED, PROVIDED THAT THE ABOVE
    COPYRIGHT NOTICE AND THIS PERMISSION NOTICE APPEAR IN ALL COPIES.
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''

import pexpect, re

class ExceptionPsh(pexpect.ExceptionPexpect):
    '''Raised for Psh exceptions.
    '''

class ExceptionErrorCode(ExceptionPsh):
    '''Raised when an program returns an error code.
    '''

    def __init__(self, string, err_code, cmd_output):

        ExceptionPsh.__init__(self,string)
        self.error  = err_code
        self.output = cmd_output

class psh (object):

    def __init__ (self,exp):

        self.exp = exp
        self.default_timeout = 30 # Seconds

    def ls (self, path=''):

        fileStr = self.run("ls %s" % path)
        return fileStr.split()

    def cd (self, path='-'):

        return self.run("cd %s" % path)

    def rm (self, path=''):

        return self.run("/bin/rm -f %s" % path)

    def cp (self, path_from='', path_to=''):

        return self.run("/bin/cp %s %s" % (path_from, path_to))

    def mv (self, path_from='', path_to=''):

        return self.run("/bin/mv %s %s" % (path_from, path_to))

    def pwd (self):

        return self.run("/bin/pwd")

    def which (self, exe_name):

        return self.run("/usr/bin/which %s" % exe_name)

    def chown (self, path, user='', group=None, recurse=False):

        xtra_flags = ""
        if recurse: xtra_flags = "-R"
        if group: group = ':' + group
        else: group = ""

        return self.run("/bin/chown %s %s%s %s" % (xtra_flags,user,group,path))

    def chmod (self, path, perms='', recurse=False):

        xtra_flags = ""
        if recurse: xtra_flags = "-R"
        return self.run("/usr/bin/chmod %s %s %s" % (xtra_flags, perms, path))

    def chattr (self, path, attrs='', recurse=False):

        xtra_flags = ""
        if recurse: xtra_flags = "-R"
        return self.run("/usr/bin/chattr %s %s %s" % (xtra_flags, attrs, path))

    def cat (self, path):

        return self.run("/bin/cat %s" % path)

    def run (self, cmd, timeout=None):

       (ret, output) = self.run_raw(cmd, timeout)
       if ret == 0: return output
       raise ExceptionErrorCode("Running command [%s] returned error [%d]"
               % (cmd,ret), ret, output)

    def run_raw(self, cmd, timeout=None):

        '''Someone contributed this, but now I've lost touch and I forget the
        motive of this. It was sort of a sketch at the time which doesn't make
        this any easier to prioritize, but it seemed important at the time. '''

        if not timeout: timeout = self.default_timeout

        self.exp.sendline("")
        if not self.exp.prompt(): raise ExceptionPsh("No prompt")
        self.exp.sendline(cmd)
        self.exp.expect_exact([cmd])
        self.exp.prompt(timeout=timeout)

        output = self.exp.before
        # Get the return code
        self.exp.sendline("echo $?")
        self.exp.expect_exact(["echo $?"])
        if not self.exp.prompt():
            raise ExceptionPsh("No prompt", 0, self.exp.before)
        try:
            reg = re.compile(b"^(\d+)")
            s = self.exp.before.strip()
            #print s
            #pdb.set_trace()
            s = reg.search(s).groups()[0]
            error_code = int(s)
        except ValueError:
            #log.error("Cannot parse %s into an int!" % self.exp.before)
            raise

        if not output[0:2] == '\r\n':
            #log.warning("Returned output lacks leading \\r\\n which may indicate a tae error")
            #log.debug2("Offending output string: [%s]" % output)
            return (error_code, output)
        else:
            return(error_code, output[2:])

