#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
import logging
import readline
import os
import sys
from abc import ABCMeta, abstractmethod
from shlex import split
import subprocess as sp
import tempfile
import getpass

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


logging.basicConfig(level='INFO', format='%(levelname)7s %(message)s')
logger = logging.getLogger(__name__)


def prompt(question, answers):
    if question[-1] != ' ':
        question = question + ' '

    return raw_prompt(question)


def yesno(question, answers={'y', 'yes', ''}):
    answer = prompt(question, answers)
    return answer.lower() in answers


def sh(command, shell=False):
    if shell:
        logger.debug('CMD: %s', command)
        sp.check_call(command, shell=True)
    else:
        cmd = split(command)
        logger.debug('CMD: %s', ' '.join(cmd))
        sp.check_call(cmd)


class Task(object):
    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config

    def pre_install(self):
        logger.debug('Pre install: %s', self.__class__.__name__)
        return True

    def post_install(self):
        logger.debug('Post install: %s', self.__class__.__name__)
        return True

    def complete_condition(self):
        return False

    @abstractmethod
    def install(self):
        pass

    def run(self):
        logger.info(PrintInColor.status('Running task %s'),
                    self.__class__.__name__)
        if not self.complete_condition():
            to_install = self.pre_install()

            if to_install:
                self.install()
                self.post_install()
            else:
                logger.info('Skipping')
        else:
            logger.info('Complete condition met')


class FetchPipeline(Task):

    def __init__(self, config):
        super(FetchPipeline, self).__init__(config)
        self.repo_url = 'https://github.com/NGTS/zlp-script.git'

    def complete_condition(self):
        return os.path.isfile('ZLP_pipeline.sh')

    def install(self):
        sh('git init')
        sh('git remote add -t \* -f origin {url}'.format(url=self.repo_url))
        sh('git checkout master')


class FetchSubmodules(Task):

    def complete_condition(self):
        return os.path.isfile('scripts/zlp-qa/run.sh')

    def install(self):
        sh('git submodule init')
        sh('git submodule update')


class InstallMiniconda(Task):

    def __init__(self, config):
        super(InstallMiniconda, self).__init__(config)
        self.script_stub = 'Miniconda-latest-Linux-x86_64.sh'
        self.download_url = 'https://repo.continuum.io/miniconda/{}'.format(
            self.script_stub)
        self.download_path = os.path.join(tempfile.gettempdir(),
                                          self.script_stub)
        self.install_path = self.config['miniconda_install_path']

    def complete_condition(self):
        return os.path.isdir(self.install_path)

    def install(self):
        sh('wget -c {} -O {}'.format(self.download_url, self.download_path))
        sh('chmod +x {}'.format(self.download_path))
        sh('{} -b -p {}'.format(self.download_path, self.install_path))

    def pre_install(self):
        # return yesno('Install miniconda to ~/anaconda? [Y/n]')
        return True


class InstallCondaPackages(Task):

    def __init__(self, config):
        super(InstallCondaPackages, self).__init__(config)
        self.install_path = self.config['miniconda_install_path']

    def complete_condition(self):
        return os.path.isfile(os.path.join(self.install_path, 'bin', 'pip'))

    def install(self):
        sh('{}/bin/conda install --yes --file requirements.conda.txt'.format(
            self.install_path))


class InstallPipPackages(InstallCondaPackages):

    def install(self):
        sh('{}/bin/pip install -r requirements.txt'.format(self.install_path))

    def complete_condition(self):
        return os.path.isdir(os.path.join(self.install_path, 'lib',
                                          'python2.7', 'site-packages',
                                          'emcee'))


class CopyTestData(Task):

    def __init__(self, config):
        super(CopyTestData, self).__init__(config)
        self.tarball_name = config['test_data_tarball_path']
        self.url = 'https://ngts.warwick.ac.uk/twiki/pub/Main/PipelineSetup/source2015.tar.gz'

    def complete_condition(self):
        return os.path.isfile(self.tarball_name)

    def pre_install(self):
        self.http_user = raw_prompt('Wiki username:')
        return True

    def install(self):
        sh('wget {url} --no-check-certificate '
           '--http-user {user} --ask-password -cO {dest}'.format(
               user=self.http_user,
               url=self.url,
               dest=self.tarball_name))


class UnpackTestData(Task):

    def __init__(self, config):
        super(UnpackTestData, self).__init__(config)
        self.tarball_name = config['test_data_tarball_path']

    def complete_condition(self):
        return os.path.isdir('source2015')

    def install(self):
        sh('tar xvf {tarball}'.format(tarball=self.tarball_name))


class Pipeline(object):

    def __init__(self, tasks):
        self.tasks = tasks

    def run(self, config):
        for task in self.tasks:
            task(config).run()


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')

    config = {
        'miniconda_install_path': os.path.expanduser('~/anaconda'),
        'test_data_tarball_path': 'source2015.tar.gz'
    }

    Pipeline([
        FetchPipeline,
        FetchSubmodules,
        InstallMiniconda,
        InstallCondaPackages,
        InstallPipPackages,
        CopyTestData,
        UnpackTestData,
    ]).run(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())
