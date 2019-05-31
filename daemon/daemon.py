"""
@author: albrdev
@date: 2019-05-14
"""

import sys, os, time, errno, signal, atexit, argparse, configparser, pwd

class Daemon(object):
    """
    Daemon base class
    Derive from this class to daemonize your application
    """
    __slots__ = ['__stdin_file', '__stderr_file', '__stdout_file', '__stderr_filepath', '__stdout_filepath', '__username', '__pid_file']

    def __init__(self, username, pid_file, stdout_filepath="/var/log/daemon.log", stderr_filepath="/var/log/daemon.log"):
        self.__stdin_file = None
        self.__stderr_file = None
        self.__stdout_file = None

        self.__stderr_filepath = stderr_filepath
        self.__stdout_filepath = stdout_filepath
        self.__username = username
        self.__pid_file = pid_file

    #def __del__(self):
        #self.cleanup()

    def init(self):
        """
        Daemonizes this application
        Sets up base behavior for the daemon
        """
        if os.fork() != 0: # Intial fork to get rid of the parent (could be a shell command line)
            os._exit(0)

        os.setsid() # Claim session ownership

        if os.fork() != 0: # Second fork to get rid of the TTY
            os._exit(0)

        passwd = pwd.getpwnam(self.__username) # Get basic user info
        if passwd.pw_gid != os.getgid(): # Sets group ID of the process to same as 'self.__username'
            os.setgid(passwd.pw_gid)

        if passwd.pw_uid != os.getuid(): # Sets user ID of the process to same as 'self.__username'
            os.setuid(passwd.pw_uid)
            os.putenv("HOME", passwd.pw_dir) # Try setting home directory aswell

        os.chdir(passwd.pw_dir) # Change current working directory
        os.umask(0o022) # Sets umask for new file creation, this should be set to the inverted value of the desired permission values

        # Redirect 'stdin' to '/dev/null'
        self.__stdin_file = open("/dev/null", 'r')
        os.dup2(self.__stdin_file.fileno(), sys.stdin.fileno())

        # Redirect 'stderr' to user defined file
        sys.stderr.flush()
        self.__stderr_file = open(self.__stderr_filepath, 'a+')
        os.dup2(self.__stderr_file.fileno(), sys.stderr.fileno())

        # Redirect 'stdout' to user defined file
        sys.stdout.flush()
        self.__stdout_file = open(self.__stdout_filepath, 'a+')
        os.dup2(self.__stdout_file.fileno(), sys.stdout.fileno())

        # Handle all signals (these could/should be handled in the overriden method 'self.signal_handler')
        for i in range(1, signal.NSIG):
            try:
                signal.signal(i, self.signal_handler)
            except (OSError, RuntimeError):
                pass

        atexit.register(self.cleanup) # Register cleanup method to be run on program exit
        self.set_pid() # Write PID file

    def cleanup(self):
        """
        Clean up daemon
        Call this from overriden method
        """
        # Close 'stdout'
        if self.__stdout_file is not None:
            self.__stdout_file.close()
            self.__stdout_file = None

        # Close 'stderr'
        if self.__stderr_file is not None:
            self.__stderr_file.close()
            self.__stderr_file = None

        # Close 'stdin'
        if self.__stdin_file is not None:
            self.__stdin_file.close()
            self.__stdin_file = None

        self.del_pid() # Delete PID file

    def signal_handler(self, num, frame):
        """
        Signal handler
        Override in subclass to custom handle signals
        """
        pass

    def loop(self):
        """
        Runs the user-defined method 'self.run' forever
        """
        while True:
            self.run()

    def get_pid(self):
        """
        Gets stored PID from file
        If this value is not None, it means a daemon process is running with the PID returned
        """
        try:
            with open(self.__pid_file, 'r') as pid_file:
                pid = int(pid_file.read().strip())
            return pid
        except IOError:
            return None

    def set_pid(self):
        """
        Writes the current process ID to PID file
        """
        pid = str(os.getpid())
        with open(self.__pid_file, 'w+') as pid_file:
            pid_file.write('{}'.format(pid))

    def del_pid(self):
        """
        Deletes the PID file (should be called on program exit)
        """
        try:
            os.remove(self.__pid_file)
        except FileNotFoundError:
            pass

    def check_pid(self, pid: int):
        """
        Check if process ID actually exists/is running
        """
        try:
            os.kill(pid, 0) # calling kill on pid with '0' doesn't affect the process (just fakes the behavior to get its status)
        except OSError as err:
            if err.errno == errno.ESRCH:
                return False
            else:
                raise
        else:
            return True

    def start(self):
        """
        Starts the daemon
        """
        pid = self.get_pid()
        if pid:
            print ("PID file \'{0}\' exists with the PID of {1}".format(self.__pid_file, pid))

            try:
                status = self.check_pid(pid)
            except:
                print("Unable to terminate daemon")
                sys.exit(1)
            else:
                if status:
                    print("PID {0} is currently running".format(pid))
                    sys.exit(1)
                else:
                    self.del_pid()

        self.init()
        self.loop()

    def stop(self):
        """
        Stops the daemon
        """
        pid = self.get_pid()
        if not pid:
            print ("PID file {0} doesn\'t exist".format(self.__pid_file))
            return

        try:
            status = self.check_pid(pid)
        except:
            print("Unable to terminate daemon")
            sys.exit(1)
        else:
            if not status:
                print("Daemon not running")
                self.del_pid()
                return

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as err:
            if err.errno == errno.ESRCH:
               self.del_pid()
            else:
                print(err)
                sys.exit(1)

    def restart(self):
        """
        Restarts the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        Called forever in the daemon main loop
        Should be overridden in the subclass
        """
        pass
