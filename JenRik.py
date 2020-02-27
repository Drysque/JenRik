#!/usr/bin/python3

import sys
import toml
import os
import subprocess
from termcolor import colored


def print_help(binary_name):
    """ Print a basic help showing how to use Jenerik """
    print(f"USAGE : {binary_name} file.jrk | init path_to_binary")
    print("\tinit\tcreate a basic test file for the given binary")


def open_file(fp):
    """ Open the toml file and parse it """
    if not fp.endswith(".toml"):
        sys.exit("You must provide valid toml file")
    try:
        f = open(fp, 'r')
    except:
        sys.exit(f"Could not open file {fp}")
    c = f.read()
    content = toml.loads(c)  # Parse the toml file
    f.close()
    return content


def init_file(fp):
    """ Create a default test file """
    test_file_name = 'test_' + fp + '.toml'

    default_file_content = [
        f"binary_path = \"{fp}\"\n\n",
        "# A sample test\n",
        "[test1]\n",
        "args = [\"-h\"]\n",
        "status = 0\n",
        "stdout=\"\"\n",
        "stderr=\"\"\n",
    ]

    if os.path.exists(test_file_name):
        sys.exit(f"{test_file_name} already exists, can't init the file")
    try:
        f = open(test_file_name, 'w')
    except:
        sys.exit(f"Could not create file {test_file_name}")
    for line in default_file_content:
        f.write(line)
    f.close()
    print(f"Initialized {test_file_name} with success")


def check_binary_validity(binary_path):
    """ Check if the binary path is a valid executable file """
    if os.path.exists(binary_path):
        if not os.access(binary_path, os.X_OK):
            sys.exit(f"{binary_path} : is not executable")
    else:
        sys.exit(f"{binary_path} : file not found")


def check_tests_validity(test_name, values):
    """ Check if all the fieds of the test are known and are valids."""
    if type(values) != dict:
        sys.exit(f"Invalid test : '{test_name} {values}'")
    known_tests_keys = ['args', 'status', 'stdout', 'stderr']
    has_args = 'args' in values.keys()
    has_status = 'status' in values.keys()

    if has_args == False or has_status == False:
        sys.exit("Missing field : " + ("'args'" * (not has_args)) +
                 (" and " * (not has_args and not has_status)) +
                 ("'status'" * (not has_status)) + " in test : " + test_name)
    for key in values:
        if key not in known_tests_keys:
            sys.exit(f"Unknown key : {key} in test {test_name}")


def check_test_file_validity(content, fp):
    """ Check if the toml test file is valid """
    binary_path = ""
    test_suite = {}

    for key in content.keys():
        if key == "binary_path":
            binary_path = content[key]
            check_binary_validity(binary_path)
        else:
            check_tests_validity(key, content[key])
            # If we arrived here then the test is valid
            test_suite[key] = content[key]

    if binary_path == "":
        sys.exit(f"Could not find binary_path key in {fp}")

    return binary_path, test_suite


class Tester:
    """ The class containing everything to run the tests """
    def __init__(self, binary_path, test_suite):
        self.test_suite = test_suite
        self.binary_path = binary_path
        self.count_tests = 0
        self.count_failed_tests = 0

    def print_test_sucess(self):
        """ print a message if test success """
        print(colored('OK', 'green'))

    def print_test_failed(self, e):
        """ print a message if test fails """
        self.count_failed_tests += 1
        print(colored('KO', 'red'), end=" : ")
        print(e)

    def check_test_results(self, values, stdout, stderr, status):
        """ check the tests results """
        if values['status'] != status:
            self.print_test_failed("Invalid exit status, "
                               f"expected {values['status']} but got {status}")
        elif values['stdout'] != "" and values['stdout'] != stdout:
            self.print_test_failed("Invalid stdout, "
                           f"expected '{values['stdout']}' but got '{stdout}'")
        elif values['stderr'] != "" and values['stderr'] != stderr:
            self.print_test_failed("Invalid stderr, "
                           f"expected '{values['stderr']}' but got '{stderr}'")
        else:
            self.print_test_sucess()

    def run_test(self, values):
        """ run the test in a subprocess """
        self.count_tests += 1
        test_args = [self.binary_path] + values['args']
        process = subprocess.Popen(test_args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        self.check_test_results(values, stdout.decode('utf-8'),
                                stderr.decode('utf-8'), process.returncode)

    def print_summary(self):
        """ print a summary of the tests results """
        count_success = self.count_tests - self.count_failed_tests
        print(f"\nSummary {self.binary_path}: {self.count_tests} tests ran")
        print(f"{count_success}\t:\t{colored('OK', 'green')}")
        print(f"{self.count_failed_tests}\t:\t{colored('KO', 'red')}")

    def launch(self):
        """ launch the tests on the test suite """
        for test in self.test_suite:
            print(f"{test} : ", end='')
            self.run_test(self.test_suite[test])
        self.print_summary()


def main(argc, argv):
    if argc == 1 or argc > 3 or argc == 3 and argv[1] != 'init':
        print_help(argv[0])
        exit(1)
    if argc == 3:
        init_file(argv[2])
        exit(0)
    elif argc == 2:
        content = open_file(argv[1])
        binary_path, test_suite = check_test_file_validity(content, argv[1])
        tester = Tester(binary_path, test_suite)
        tester.launch()


if __name__ == '__main__':
    main(len(sys.argv), sys.argv)
