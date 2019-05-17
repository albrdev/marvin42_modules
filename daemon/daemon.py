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
        self.stdin_file = None
        self.stderr_file = None
        self.stdout_file = None

        self.__stdout_filepath = stdout
        self.__stderr_filepath = stderr
        self.__username = username
        self.__pid_file = pid_file

    def __del__(self):
        if self.stdin_file is not None:
            close(self.stdout_file)

        if self.stdin_file is not None:
            close(self.stderr_file)

        if self.stdin_file is not None:
            close(self.stdin_file)

        sefl.cleanup()

    def init(self):
        if os.fork() != 0:
            os._exit(0)

        os.setsid()

        if os.fork() != 0:
            os._exit(0)

        #atexit.register(self.cleanup)
            
        passwd = pwd.getpwnam(self.__username)
        if passwd.pw_gid != os.getgid():
            os.setgid(passwd.pw_gid)

        if passwd.pw_uid != os.getuid():
            os.setuid(passwd.pw_uid)
            os.putenv("HOME", passwd.pw_dir)

        os.chdir(passwd.pw_dir)
        os.umask(0o022)

        self.stdin_file = open("/dev/null", 'r')
        os.dup2(self.stdin_file.fileno(), sys.stdin.fileno())

        sys.stderr.flush()
        self.stderr_file = open(self.__stderr_filepath, 'a+')
        os.dup2(self.stderr_file.fileno(), sys.stderr.fileno())

        sys.stdout.flush()
        self.stdout_file = open(self.__stdout_filepath, 'a+')
        os.dup2(self.stdout_file.fileno(), sys.stdout.fileno())

        for i in range(1, signal.NSIG):
            try:
                signal.signal(i, self.signal_handler)
            except (OSError, RuntimeError):
                pass

        self.set_pid()

    def cleanup(self):
        self.del_pid()

    def signal_handler(self, num, frame):
        pass

    def loop(self):
        while True:
            self.run()

    def get_pid(self):
        try:
            with open(self.__pid_file, 'r') as pid_file:
                pid = int(pid_file.read().strip())
            return pid
        except IOError:
            return

    def set_pid(self):
        pid = str(os.getpid())
        with open(self.__pid_file, 'w+') as pid_file:
            pid_file.write('{}'.format(pid))

    def del_pid(self):
        try:
            os.remove(self.__pid_file)
        except FileNotFoundError:
            pass

    def start(self):
        if self.get_pid():
            print ('PID file {0} exists. Is the deamon already running?'.format(self.__pid_file))
            sys.exit(1)

        self.init()
        self.loop()

    def stop(self):
        pid = self.get_pid()
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
        except OSError as err:
            print(err)
            sys.exit(1)

    def restart(self):
        self.stop()
        time.sleep(0.5)
        self.start()

    def run(self):
        pass
