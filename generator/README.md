PKGBUILD GENERATOR
==================

Run ```./pkgbuild_generator.py``` to generate a PGKBUILD with the latest version info and checksums.
Generating the checksums takes some time and there is no feedback unless an error occurs so please be patient.

This script is created to aid the maintainers but can of course be used if Spotify is recently updated.
Please do not forget to mark the package as outdated on [AUR](https://aur.archlinux.org/packages/spotify)
if you *have* to use the generator to install Spotify.

## Requirements

The script is written in python and requires a few libraries:

1. Python (only tested on python3)
1. BeautifulSoup (pip install beautifulsoup4)
1. Jinja2 (pip install jinja2)

## Maintenance

General changes in the PKGBUILD have to be made in the jinja template file: **PKGBUILD.j2**.
There are also a few hardcoded values that might be subject to change.

* Mirror url - The mirror url is provided at the very bottom.
  It should point to the URL that lists the debian packages.
* Version extraction regexp - There is a regular expression at the top of the ```Package``` class. 
  When the version info variables in PKGBUILD are empty, the regular expresion no longer matches and needs to be updated. 

All "constants" are either provided as class properties or at the bottom of the script
 where composition and execution takes place. 

## TODO

* Dynamically generate info on static (included in repository) sources.
* ~~Run makepkg --printsrcinfo to update .SRCINFO.~~
* Provide feedback when generating checksums.