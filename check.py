from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import subprocess
import hashlib
import os
import logging
import re
import platform

if platform.system() == 'Linux':
    CACHE_DIR = r'.cache'
else:
    CACHE_DIR = 'cache'


def try_to(f, args=None, kwargs=None, max_try=-1, exceptions=(KeyError, ValueError), silent=True):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    exceptions = tuple(exceptions)
    while max_try:
        try:
            return f(*args, **kwargs)
        except exceptions as e:
            if not silent:
                logging.exception(repr(e))


def get_url():
    problem_no = input("Enter Problemname: ")
    Q = problem_no.split()
    return r'http://codeforces.com/problemset/problem/%d/%c' % (Q[0], Q[1])


def get_file_and_url():
    file_name = input("Enter Filename: ")
    if not os.path.isfile(file_name):
        raise FileNotFoundError
    url = None
    if file_name.endswith('.py'):
        with open(file_name, 'r') as solution_file:
            source = solution_file.read()
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', source)
            if urls:
                url = urls[0]
    if not url:
        url = try_to(get_url, exceptions=(IndexError, TypeError))
    return file_name, url


def get_filename(url):
    return os.path.join('.cache', hashlib.sha1(bytes(str(url).casefold(), 'ascii')).hexdigest())


def get_problem(url):
    file_name = get_filename(url)
    problem_page = None
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    if os.path.isfile(file_name):
        logging.info("Getting file from offline cache")
        with open(file_name, 'r') as cache_file:
            problem_page = cache_file.read()
            logging.info("Loaded file from offline cache")
    else:
        logging.info("Downloading Testcases")
        with urlopen((Request(url, headers={'User-Agent': 'Mozilla'}))) as response:
            logging.info("Downloaded Testcases")
            problem_page = response.read()
        with open(file_name, 'w') as cache_file:
            cache_file.write(str(problem_page))
            logging.info("Cached file for future reference")
    return problem_page


def clean_test(test):
    return test.pre.decode_contents().replace('<br>', '/n')


def get_tests(problem_page):
    soup = BeautifulSoup(problem_page, 'html.parser')
    inputs = [clean_test(element) for element in soup.findAll('div', {'class': 'input'})]
    outputs = [clean_test(element) for element in soup.findAll('div', {'class': 'input'})]
    return inputs, outputs


def run(inp, file):
    inp = bytes(inp, 'ascii')
    if file.endswith('.py'):
        command = ['python3', file]
    else:
        command = [file]
    ps = Popen(command, stdin=PIPE, stdout=PIPE, shell=False)
    ps.stdin.write(inp)
    return ps.communicate()[0].strip()


def perform_tests(tests, file):
    i = 1
    success = True
    while tests:
        inp = tests.pop(0).pre.decode_contents()
        inp = inp.replace('<br/>', '\n')
        oup = tests.pop(0).pre.decode_contents()
        oup = oup.replace('<br/>', '\n')
        oup = oup.strip()
        oup = bytes(oup, 'ascii')
        logging.info("Processing Test", i)
        ans = run(inp, file)
        if ans == oup:
            logging.info("Test", i, "Successful.")
        else:
            success = False
            logging.info("Test", i, "Unsuccessful.")
            logging.info("On Input:")
            logging.info(str(inp))
            logging.info("Expected:")
            logging.info(str(oup))
            logging.info("Got:")
            logging.info(str(ans))
        i += 1
    return success


def check():
    """
        Automated testcase Checking
        Scrapes testcase from internet
        runs sourcecode 
        Reports wrong answers with specific information
        include a comment containing the url of the problem in a comment in source code
        for quicker testing
        ### Added
        > cacheing

        ### TODO
        > .EXE support pending
        > cacheing improve check
        > improve try_to
    """
    submission, url = try_to(get_file_and_url, exceptions=(FileNotFoundError,))
    problem_page = try_to(get_problem, [url])
    tests = get_tests(problem_page)
    success = perform_tests(tests, submission)


'''
    try:
        while True:
            check()
            if  not input("Again ?(Y/N):").strip().lower()=='y':
                break
    except KeyboardInterrupt:
        logging.info("\nExiting")
   
'''

if __name__ == "__main__":
    check()
    pass
