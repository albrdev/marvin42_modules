# Daemon base class 
#@author: albrdev
#"""

import sys, os, time, errno, signal, atexit, argparse, configparser, pwd

class Daemon(object):
    __slots__ = ['__stdin_file', '__stderr_file', '__stdout_file', '__stderr_filepath', '__stdout_filepath', '__username', '__pid_file']

    def __init__(self, username, pid_file, stdout_filepath="/var/log/daemon.log", stderr_filepath="/var/log/daemon.log"):
        self.__stdin_file = None
        self.__stderr_file = None
        self.__stdout_file = None

        self.__stderr_filepath = stderr_filepath
        self.__stdout_filepath = stdout_filepath
        self.__username = username
        self.__pid_file = pid_file

    def __del__(self):
        self.cleanup()

    def init(self):
        if os.fork() != 0:
            os._exit(0)

        os.setsid()

        if os.fork() != 0:
            os._exit(0)

        passwd = pwd.getpwnam(self.__username)
        if passwd.pw_gid != os.getgid():
            os.setgid(passwd.pw_gid)

        if passwd.pw_uid != os.getuid():
            os.setuid(passwd.pw_uid)
            os.putenv("HOME", passwd.pw_dir)

        os.chdir(passwd.pw_dir)
        os.umask(0o022)

        self.__stdin_file = open("/dev/null", 'r')
        os.dup2(self.__stdin_file.fileno(), sys.stdin.fileno())

        sys.stderr.flush()
        self.__stderr_file = open(self.__stderr_filepath, 'a+')
        os.dup2(self.__stderr_file.fileno(), sys.stderr.fileno())

        sys.stdout.flush()
        self.__stdout_file = open(self.__stdout_filepath, 'a+')
        os.dup2(self.__stdout_file.fileno(), sys.stdout.fileno())

        for i in range(1, signal.NSIG):
            try:
                signal.signal(i, self.signal_handler)
            except (OSError, RuntimeError):
                pass

        atexit.register(self.cleanup)
        self.set_pid()

    def cleanup(self):
        if self.__stdout_file is not None:
            self.__stdout_file.close()
            self.__stdout_file = None

        if self.__stderr_file is not None:
            self.__stderr_file.close()
            self.__stderr_file = None

        if self.__stdin_file is not None:
            self.__stdin_file.close()
            self.__stdin_file = None

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
            return None

    def set_pid(self):
        pid = str(os.getpid())
        with open(self.__pid_file, 'w+') as pid_file:
            pid_file.write('{}'.format(pid))

    def del_pid(self):
        try:
            os.remove(self.__pid_file)
        except FileNotFoundError:
            pass

    def check_pid(self, pid: int):
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                return False
            else:
                return None

        return True

    def start(self):
        pid = self.get_pid()
        if pid:
            print ("PID file \'{0}\' exists with the PID of {1}".format(self.__pid_file, pid))
            if self.check_pid(pid) == False:
                print("PID {0} is not running".format(pid))
            else:
                print("PID {0} is currently running".format(pid))

            sys.exit(1)

        self.init()
        self.loop()

    def stop(self):
        pid = self.get_pid()
        if not pid:
            print ("PID file {0} doesn\'t exist".format(self.__pid_file))
            return

        status = self.check_pid(pid)
        if status == False:
            print("Daemon not running")
            self.del_pid()
            return
        elif status == None:
            print("Unable to terminate daemon")
            sys.exit(1)

        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            if err.errno == errno.ESRCH:
               self.del_pid()
            else:
                print(err)
                sys.exit(1)

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        pass
