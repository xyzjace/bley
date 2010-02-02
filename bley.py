#!/usr/bin/env python
#
# Copyright (c) 2009 Evgeni Golov <evgeni.golov@uni-duesseldorf.de>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

import os
import sys

from twisted.internet import reactor

try:
    from twisted.scripts import _twistd_unix as twistd
except:
    from twisted.scripts import twistd

from BleyWorker import BleyPolicyFactory
from BleyCleaner import BleyCleaner
import settings

if settings.log_file == 'syslog':
    import syslog
    syslog.openlog('bley', syslog.LOG_PID, syslog.LOG_MAIL)
    settings.logger = syslog.syslog
elif settings.log_file in ['-', '']:
    settings.logger = sys.stdout.write
else:
    settings.logger = open(settings.log_file, 'a').write

__CREATE_DB_QUERY = '''
  CREATE TABLE IF NOT EXISTS bley_status
  (
    ip VARCHAR(39) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    last_action TIMESTAMP NOT NULL,
    sender VARCHAR(254),
    recipient VARCHAR(254),
    fail_count INT DEFAULT 0
  );
'''
__CREATE_DB_QUERY_PG = '''
  CREATE TABLE bley_status
  (
    ip VARCHAR(39) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    last_action TIMESTAMP NOT NULL,
    sender VARCHAR(254),
    recipient VARCHAR(254),
    fail_count INT DEFAULT 0
  );
'''
__CHECK_DB_QUERY_PG = '''
  SELECT tablename FROM pg_catalog.pg_tables WHERE tablename = 'bley_status'
'''

def bley_start():

    db = settings.database.connect(settings.dsn)
    dbc = db.cursor()
    if settings.database.__name__ == 'psycopg2':
        dbc.execute(__CHECK_DB_QUERY_PG)
        if not dbc.fetchall():
            dbc.execute(__CREATE_DB_QUERY_PG)
    else:
        dbc.execute(__CREATE_DB_QUERY)
    db.commit()
    dbc.close()
    db.close()

#    cleaner = BleyCleaner(settings)
#    cleaner.setDaemon(1)
#    cleaner.start()

    reactor.listenTCP(settings.listen_port, BleyPolicyFactory(settings), interface=settings.listen_addr)
    reactor.addSystemEventTrigger('before', 'shutdown', bley_stop)
    twistd.checkPID(settings.pid_file)
    #twistd.daemonize()
    if settings.pid_file:
        writePID(settings.pid_file)
    reactor.run()

def bley_stop():
    if settings.pid_file:
        delPID(settings.pid_file)
    if settings.log_file == 'syslog':
        syslog.closelog()

def writePID(pidfile):
    # Create a PID file
    pid = str(os.getpid())
    pf = open(pidfile, "w")
    pf.write("%s\n" % pid)
    pf.close()

def delPID(pidfile):
    if os.path.exists(pidfile):
        os.remove(pidfile)

bley_start()
