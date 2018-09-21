#!/usr/bin/env python
import re
from _sha256 import sha256
from optparse import OptionParser
from subprocess import call
from urllib import request

import output
import jinja2
from bs4 import BeautifulSoup
from jinja2 import FileSystemLoader
from os import path


MIRROR = 'http://repository.spotify.com/pool/non-free/s/spotify-client/'
CHUNK_SIZE = 1024 * 1024 * 4  # 4MiB
stdout = output.Output()


class PkgBuildGenerator(object):
    _generator_dir = path.dirname(path.abspath(__file__))
    _target_dir = path.dirname(_generator_dir)
    _template = 'PKGBUILD.j2'
    _target = _target_dir + '/PKGBUILD'
    _pkg_type = 'deb'

    def __init__(self, mirror: str):
        if mirror[-1] is not '/':
            mirror += '/'
        self._mirror = mirror

    def generate(self):
        package_data = self._create_package_data()
        template_data = self._build_template_data(package_data)

        env = jinja2.Environment(loader=FileSystemLoader(self._generator_dir))
        t = env.get_template(self._template)
        with open(self._target, 'w') as f:
            f.write(t.render(template_data))

    @property
    def target_dir(self):
        return self._target_dir

    def _build_template_data(self, package_data: dict) -> dict:
        x86_64: Package = package_data['x86_64']

        template_data = {
            'mirror': self._mirror,
            'pkgver': x86_64.pkgver,
            'anotherpkgver': x86_64.pkgver_other,
            'amd64_pkgrel': x86_64.pkgrel,
            'sha256sums_x86_64': x86_64.shasum
        }

        return template_data

    def _create_package_data(self) -> dict:
        package_data = {}
        files = self._list_files()
        # FIXME: list empty exception
        files = self._filter_old(files)

        for file in files:
            package = Package(self._mirror, file)
            package_data[package.arch] = package

        return package_data

    def _list_files(self) -> list:
        page = request.urlopen(self._mirror).read()
        bs = BeautifulSoup(page, 'html.parser')
        return [a.get('href') for a in bs.find_all('a') if a.get('href').endswith(self._pkg_type)]

    def _filter_old(self, files: list) -> list:
        files.sort()
        latest = Package(self._mirror, files[-1]).pkgver
        return [file for file in files if latest in file]


class Package(object):
    _version_regex = 'spotify-client_([0-9.]+)\.([^-]+)-([0-9]+)'

    def __init__(self, mirror: str, file: str):
        if mirror[-1] is not '/':
            mirror += '/'
        self._mirror = mirror
        self._file = file
        self._version_match = re.compile(self._version_regex).match(file)

    @property
    def file(self) -> str:
        return self._file

    @property
    def arch(self) -> str:
        return 'x86_64' if 'amd64' in self.file else None

    @property
    def shasum(self) -> str:
        stdout.print('Calculating checksum of {}'.format(self.file))
        response = request.urlopen(self._mirror + self.file)
        length = int(response.headers.get('content-length'))
        checksum = sha256()
        count = 0
        for chunk in iter(lambda: response.read(CHUNK_SIZE), b''):
            checksum.update(chunk)
            count += len(chunk)
            stdout.progress(count, length)

        return checksum.hexdigest()

    @property
    def pkgver(self) -> str:
        return self._version_match.group(1)

    @property
    def pkgver_other(self) -> str:
        return self._version_match.group(2)

    @property
    def pkgrel(self) -> int:
        return int(self._version_match.group(3))


if __name__ == '__main__':
    # handle cmdline args
    parser = OptionParser()
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="Suppress output on STDOUT")
    (options, args) = parser.parse_args()

    stdout = output.Output() if options.quiet else output.CmdLineOutput()

    # Generate PKGBUILD
    stdout.print('Generating PKGBUILD ...')
    generator = PkgBuildGenerator(MIRROR)
    generator.generate()

    # Generate .SRCINFO
    stdout.print('Generating .SRCINFO ...')
    with open('{}/.SRCINFO'.format(generator.target_dir), 'w') as srcinfo:
        call(['makepkg', '--printsrcinfo'], stdout=srcinfo, cwd=generator.target_dir)
