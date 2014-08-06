# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
The I{metrics} module defines classes and other resources
designed for collecting and reporting performance metrics.
"""

import time
from logging import getLogger
from suds import *
from math import modf

log = getLogger(__name__)

class Timer:

    def __init__(self):
        self.started = 0
        self.stopped = 0

    def start(self):
        self.started = time.time()
        self.stopped = 0
        return self

    def stop(self):
        if self.started > 0:
            self.stopped = time.time()
        return self

    def duration(self):
        return ( self.stopped - self.started )

    def __str__(self):
        if self.started == 0:
            return 'not-running'
        if self.started > 0 and self.stopped == 0:
            return 'started: %d (running)' % self.started
        duration = self.duration()
        jmod = ( lambda m : (m[1], m[0]*1000) )
        if duration < 1:
            ms = (duration*1000)
            return '%d (ms)' % ms           
        if duration < 60:
            m = modf(duration)
            return '%d.%.3d (seconds)' % jmod(m)
        m = modf(duration/60)
        return '%d.%.3d (minutes)' % jmod(m)
