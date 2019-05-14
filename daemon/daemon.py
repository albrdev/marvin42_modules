# Daemon base class 
#@author: albrdev
#"""

import argparse
import configparser
import atexit
import errno
import datetime
import os
import signal
import sys
import time
import pwd

class Daemon(object):
    __slots__ = ['__stdout', '__stderr', '__username', '__pid_file']

    def __init__(self, username, pid_file, stdout='/var/log/daemon.log', stderr='/var/log/daemon.log'):
        self.__stdout = stdout
        self.__stderr = stderr
        self.__username = username
        self.__pid_file = pid_file

    def __del__(self):
        pass

    def init(self):
        """ There shined a shiny daemon, In the middle, Of the road... """
        # fork 1 to spin off the child that will spawn the deamon.
        if os.fork() != 0:
            os._exit(0)

        # This is the child.
        # 1. cd to root for a guarenteed working dir.
        # 2. clear the session id to clear the controlling TTY.
        # 3. set the umask so we have access to all files created by the daemon.
        os.setsid()

        # fork 2 ensures we can't get a controlling ttd.
        if os.fork() != 0:
            os._exit(0)
            
        passwd = pwd.getpwnam(self.__username)
        if passwd.pw_gid != os.getgid():
            os.setgid(passwd.pw_gid)

        if passwd.pw_uid != os.getuid():
            os.setuid(passwd.pw_uid)
            print("passwd:", passwd.pw_dir)
            os.putenv("HOME", passwd.pw_dir)

        os.chdir(passwd.pw_dir)
        os.umask(0o022)

        # This is a child that can't ever have a controlling TTY.
        # Now we shut down stdin and point stdout/stderr at log files.

        #sys.stdin.close()
        #sys.stderr.close()
        #sys.stdout.close()

        # stdin
        with open('/dev/null', 'r') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())

        # stderr - do this before stdout so that errors about setting stdout write to the log file.
        #
        # Exceptions raised after this point will be written to the log file.
        sys.stderr.flush()
        #with open(self.__stderr, 'a+', 0) as stderr:
        with open(self.__stderr, 'w+') as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())

        # stdout
        #
        # Print statements after this step will not work. Use sys.stdout
        # instead.
        sys.stdout.flush()
        #with open(self.__stdout, 'a+', 0) as stdout:
        with open(self.__stdout, 'w+') as stdout:
            os.dup2(stdout.fileno(), sys.stdout.fileno())

        # Write pid file
        # Before file creation, make sure we'll delete the pid file on exit!
        atexit.register(self.cleanup)

        for i in range(1, signal.NSIG):
            try:
                signal.signal(i, self.handle_signals)
            except (OSError, RuntimeError):
                pass

        pid = str(os.getpid())
        with open(self.__pid_file, 'w+') as pid_file:
            pid_file.write('{0}'.format(pid))

    def loop(self):
        while True:
            self.run()

    def cleanup(self):
        self.del_pid()

    def handle_signals(self, num, frame):
        pass

    def get_pid_by_file(self):
        try:
            with open(self.__pid_file, 'r') as pid_file:
                pid = int(pid_file.read().strip())
            return pid
        except IOError:
            return

    def del_pid(self):
        try:
            os.remove(self.__pid_file)
        except FileNotFoundError:
            pass

    def start(self):
        """ Start the daemon. """
        print ('Starting...')
        if self.get_pid_by_file():
            print ('PID file {0} exists. Is the deamon already running?'.format(self.__pid_file))
            sys.exit(1)

        self.init()
        self.loop()

    def stop(self):
        """ Stop the daemon. """
        print ('Stopping...')
        pid = self.get_pid_by_file()
        if not pid:
            print ('PID file {0} doesn\'t exist. Is the daemon not running?'.format(self.__pid_file))
            return

        try:
            os.kill(pid, 0)
        except OSError:
            if err.errno == errno.ESRCH:
                print("Daemon not running")
                self.del_pid()
                return
            elif err.errno == errno.EPERM:
                print("Permission denied")
            else:
                print(err)

            sys.exit(1)

        try:
            os.kill(pid, signal.SIGTERM)
            self.del_pid()
            time.sleep(0.1)
        except OSError as err:
            print(err)
            sys.exit(1)

    def restart(self):
        """ Restart the deamon. """
        self.stop()
        time.sleep(0.5)
        self.start()

    def run(self):
        pass
