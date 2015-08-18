#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import logging
import readline
from multiprocessing import cpu_count
import os
import sys
from abc import ABCMeta, abstractmethod
from shlex import split
import subprocess as sp
import tempfile
import getpass
from contextlib import contextmanager

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
try:
    if sys.version_info.major == 3:
        raw_prompt = input
    else:
        raw_prompt = raw_input
except AttributeError:
    # Python <=2.6 :(
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


def yesno(question, answers=set(['y', 'yes', ''])):
    answer = prompt(question, answers)
    return answer.lower() in answers


@contextmanager
def cd(path):
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)


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
        sh('git submodule foreach git submodule init')
        sh('git submodule foreach git submodule update')


class InstallMiniconda(Task):

    def __init__(self, config):
        super(InstallMiniconda, self).__init__(config)
        self.script_stub = 'Miniconda-latest-Linux-x86_64.sh'
        self.download_url = 'https://repo.continuum.io/miniconda/{stub}'.format(
            stub=self.script_stub)
        self.download_path = os.path.join(tempfile.gettempdir(),
                                          self.script_stub)
        self.install_path = self.config['miniconda_install_path']

    def complete_condition(self):
        return os.path.isdir(self.install_path)

    def install(self):
        sh('wget -c {url} -O {path}'.format(url=self.download_url,
            path=self.download_path))
        sh('chmod +x {path}'.format(path=self.download_path))
        sh('{download} -b -p {install}'.format(
            download=self.download_path,
            install=self.install_path))

    def pre_install(self):
        return yesno('Install miniconda to ~/anaconda? [Y/n]')


class InstallCondaPackages(Task):

    def __init__(self, config):
        super(InstallCondaPackages, self).__init__(config)
        self.install_path = self.config['miniconda_install_path']
        self.packages = ['astropy', 'ipython', 'jinja2', 'matplotlib', 'numpy',
                         'pip', 'pytest', 'python', 'python-dateutil', 'pytz',
                         'readline', 'scipy', 'setuptools', 'six']

    def complete_condition(self):
        return os.path.isfile(os.path.join(self.install_path, 'bin', 'pip'))

    def install(self):
        sh('{path}/bin/conda install --yes {packages}'.format(
            path=self.install_path,
            packages=' '.join(self.packages)))


class InstallPipPackages(InstallCondaPackages):

    def __init__(self, config):
        super(InstallPipPackages, self).__init__(config)
        self.packages = ['emcee', 'fitsio', 'pycrypto']

    def install(self):
        sh('{path}/bin/pip install {packages}'.format(
            path=self.install_path,
            packages=' '.join(self.packages)))

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


class CloneCustomCasutools(Task):

    def __init__(self, config):
        super(CloneCustomCasutools, self).__init__(config)
        self.clone_path = self.config['casutools_clone_path']

    def complete_condition(self):
        return os.path.isdir(self.clone_path)

    def install(self):
        sh('git clone https://github.com/NGTS/custom-casutools.git {path}'.format(
            path=self.clone_path))


class CompileSource(Task):

    def __init__(self, config):
        super(CompileSource, self).__init__(config)


class InstallCasutools(Task):

    def __init__(self, config):
        super(InstallCasutools, self).__init__(config)
        self.install_location = os.path.realpath(self.config['install_prefix'])
        self.clone_path = self.config['casutools_clone_path']

    def complete_condition(self):
        return os.path.isfile(
            os.path.join(self.install_location, 'bin', 'imcore'))

    def install(self):
        with cd(os.path.join(self.clone_path, 'casutools-src')):
            sh('./configure --prefix={prefix} --with-wcs={prefix} '
               '--with-cfitsio={prefix}'.format(
                   prefix=self.install_location))
            sh('make -j {:d}'.format(cpu_count()))
            sh('make install')


class Compile(Task):

    def __init__(self, key):
        self.key = key

    def __call__(self, config):
        self.config = config
        self.prefix = os.path.realpath(self.config['install_prefix'])
        return self

    def pre_install(self):
        self.url = self.config[self.key]['url']
        return True

    def complete_condition(self):
        return os.path.isfile(self.config[self.key]['complete'].format(
            prefix=self.prefix))

    def install(self):
        temp_path = tempfile.gettempdir()
        stub = os.path.basename(self.url)
        download_path = os.path.join(temp_path, stub)
        sh('wget {url} -cO {path}'.format(url=self.url, path=download_path))
        with cd(temp_path):
            sh('tar xvf {path}'.format(path=stub))
            with cd(self.config[self.key]['unpacked_dir']):
                extra_args = self.config[self.key].get(
                    'extra_compile_args', '').format(self.prefix)
                sh('./configure --prefix={prefix} {extra_args}'.format(
                    prefix=self.prefix,
                    extra_args=extra_args))
                sh('make -j {:d}'.format(cpu_count()))
                sh('make install')


class CloneCASUDetrender(Task):

    def __init__(self, config):
        super(CloneCASUDetrender, self).__init__(config)
        self.hostname = 'ngtshead.warwick.ac.uk'
        self.repo = '/home/sw/git/casu-lightcurves.git'
        self.username = self.config['ngtshead_username']

    def complete_condition(self):
        return os.path.isdir('casu-lightcurves')

    def install(self):
        sh('git clone {user}@{hostname}:{repo}'.format(
            user=self.username,
            hostname=self.hostname,
            repo=self.repo))
        with cd('casu-lightcurves'):
            sh('git submodule init')
            sh('git submodule update')


class CloneSysrem(Task):

    def __init__(self, config):
        super(CloneSysrem, self).__init__(config)

        self.hostname = 'ngtshead.warwick.ac.uk'
        self.repo = '/home/sw/git/sysrem.git'
        self.username = self.config['ngtshead_username']

    def complete_condition(self):
        return os.path.isdir('sysrem')

    def install(self):
        sh('git clone {user}@{hostname}:{repo}'.format(
            user=self.username,
            hostname=self.hostname,
            repo=self.repo))


class InstallCASUDetrender(Task):

    def __init__(self, config):
        super(InstallCASUDetrender, self).__init__(config)
        self.prefix = os.path.realpath(self.config['install_prefix'])

    def complete_condition(self):
        return os.path.isfile(os.path.join(self.prefix, 'bin',
                                           'lightcurves-casu'))

    def install(self):
        with cd('casu-lightcurves'):
            sh('PKG_CONFIG_PATH={prefix}/lib/pkgconfig make PREFIX={prefix} '
               'PGPLOT_INC= PGPLOT_LIBS= PGPLOT_SRCS='.format(
                   prefix=self.prefix),
               shell=True)
            sh('PKG_CONFIG_PATH={prefix}/lib/pkgconfig make PREFIX={prefix} '
               'PGPLOT_INC= PGPLOT_LIBS= PGPLOT_SRCS= install'.format(
                   prefix=self.prefix),
               shell=True)


class InstallSysrem(Task):

    def __init__(self, config):
        super(InstallSysrem, self).__init__(config)
        self.prefix = os.path.realpath(self.config['install_prefix'])

    def complete_condition(self):
        return os.path.isfile(os.path.join(self.prefix, 'bin', 'sysrem'))

    def install(self):
        with cd('sysrem'):
            # Add make variables for this system
            hostname = sp.check_output(['hostname', '-s']).strip()
            text = '''CFITSIODIR := {prefix}
CC := g++
FORT := gfortran

FORTFLAGS := -ffixed-line-length=132
COMMON := -fopenmp -O2
'''.format(prefix=self.prefix)
            with open('Makefile.{hostname}'.format(
                hostname=hostname), 'w') as outfile:
                outfile.write(text)

            sh('make -j {:d}'.format(cpu_count()))
            sh('make install PREFIX={prefix}'.format(prefix=self.prefix))


class Pipeline(object):

    def __init__(self, tasks):
        self.tasks = tasks

    def run(self, config):
        for task in self.tasks:
            task(config).run()


def print_environment_setup(config):
    prefix = os.path.realpath(config['install_prefix'])
    miniconda = os.path.realpath(config['miniconda_install_path'])

    text = '''To complete the installation, ensure that

    {prefix}/bin and
    {miniconda}/bin

are on your PATH, and

    {prefix}/lib

is on your LD_LIBRARY_PATH'''.format(miniconda=miniconda,
                                     prefix=prefix)
    logger.info(text)


def main():
    config = {
        'miniconda_install_path': os.path.expanduser('~/anaconda'),
        'test_data_tarball_path': 'source2015.tar.gz',
        'casutools_clone_path': 'casutools',
        'ngtshead_username': raw_prompt('ngtshead user name: '),
        'install_prefix': '.',
        'wcslib': {
            'url': 'ftp://ftp.atnf.csiro.au/pub/software/wcslib/wcslib.tar.bz2',
            'complete': '{prefix}/lib/libwcs.a',
            'unpacked_dir': 'wcslib-5.9',
        },
        'cfitsio': {
            'url':
            'ftp://heasarc.gsfc.nasa.gov/software/fitsio/c/cfitsio3370.tar.gz',
            'complete': '{prefix}/lib/libcfitsio.a',
            'unpacked_dir': 'cfitsio',
        },
    }

    Pipeline([
        FetchPipeline,
        FetchSubmodules,
        InstallMiniconda,
        InstallCondaPackages,
        InstallPipPackages,
        CopyTestData,
        UnpackTestData,
        Compile('cfitsio'),
        Compile('wcslib'),
        CloneCustomCasutools,
        InstallCasutools,
        CloneCASUDetrender,
        InstallCASUDetrender,
        CloneSysrem,
        InstallSysrem,
    ]).run(config)

    print_environment_setup(config)


if __name__ == '__main__':
    main()
