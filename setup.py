#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
import logging
import readline
import os
import sys
from abc import ABCMeta, abstractmethod

# Set up readline for nicer prompt work
histfile = os.path.join(os.path.expanduser('~'), '.pipeline-install-hist')
try:
    readline.read_history_file(histfile)
except IOError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)
del histfile

# Python 3
if sys.version_info.major == 3:
    raw_prompt = input
else:
    raw_prompt = raw_input

class PrintInColor(object):
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    LIGHT_PURPLE = '\033[94m'
    PURPLE = '\033[95m'
    END = '\033[0m'

    @classmethod
    def error(cls, s):
        return cls.RED + s + cls.END

    @classmethod
    def status(cls, s):
        return cls.GREEN + s + cls.END

logging.basicConfig(
    level='INFO', format='%(levelname)7s %(message)s')
logger = logging.getLogger(__name__)

def prompt(question, answers):
    if question[-1] != ' ':
        question = question + ' '

    return raw_prompt(question)

def yesno(question, answers={'y', 'yes', ''}):
    answer = prompt(question, answers)
    return answer.lower() in answers

class Task(object):
    __metaclass__ = ABCMeta

    def pre_install(self):
        logger.debug('Pre install: %s', self.__class__.__name__)

    def post_install(self):
        logger.debug('Post install: %s', self.__class__.__name__)

    def complete_condition(self):
        return False

    @abstractmethod
    def install(self):
        pass

    def run(self):
        self.pre_install()
        if not self.complete_condition():
            logger.debug('Complete condition met')
            self.install
        self.post_install()


class ClonePipelineTask(Task):
    def complete_condition(self):
        return os.path.isfile('ZLP_pipeline.sh')
    
    def install(self):
        pass

def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')

    ClonePipelineTask().run()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())
