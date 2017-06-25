#!/usr/bin/env python
import re
from _sha256 import sha256
from urllib import request

import jinja2
from bs4 import BeautifulSoup
from jinja2 import FileSystemLoader


class PkgBuildGenerator(object):
    _template = 'PKGBUILD.j2'
    _target = 'PKGBUILD'
    _pkg_type = 'deb'

    def __init__(self, mirror: str) -> object:
        if mirror[-1] is not '/':
            mirror += '/'
        self._mirror = mirror

    def generate(self):
        package_data = self._create_package_data()
        template_data = self._build_template_data(package_data)

        env = jinja2.Environment(loader=FileSystemLoader('.'))
        t = env.get_template(self._template)
        with open(self._target, 'w') as f:
            f.write(t.render(template_data))

    def _build_template_data(self, package_data: dict) -> dict:
        x86_64: Package = package_data['x86_64']
        i686: Package = package_data['i686']

        template_data = {
            'mirror': self._mirror,
            'pkgver': x86_64.pkgver,
            'anotherpkgver': x86_64.pkgver_other,
            'amd64_pkgrel': x86_64.pkgrel,
            'i386_pkgrel': i686.pkgrel,
            'sha256sums_x86_64': x86_64.shasum,
            'sha256sums_i686': i686.shasum,
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

    def __init__(self, mirror: str, file: str) -> object:
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
        return 'x86_64' if 'amd64' in self.file else 'i686'

    @property
    def shasum(self) -> str:
        contents = request.urlopen(self._mirror + self.file).read()
        return sha256(contents).hexdigest()

    @property
    def pkgver(self) -> str:
        return self._version_match.group(1)

    @property
    def pkgver_other(self) -> str:
        return self._version_match.group(2)

    @property
    def pkgrel(self) -> int:
        return self._version_match.group(3)


generator = PkgBuildGenerator('http://repository.spotify.com/pool/non-free/s/spotify-client/')
generator.generate()
