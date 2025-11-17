mp3_linter
==========

Opinionated & consistent ID3 linter & fixer

## Features

- Scan an entire folder of MP3s for ID3 tag issues
- Fix issues automatically whenever possible: image resize, renaming and tag issues
- Reports errors in clear colorcoded entries per file, and summarizes the results
- See "Why & How" for an explanation of how the linter works

## Install

### Pip

```bash
pip install --user -I git+https://github.com/Jelmerro/mp3_linter
```

### [Github](https://github.com/Jelmerro/mp3_linter/releases)

Download a stable installer or executable for your platform from Github.

### [Fedora](https://jelmerro.nl/fedora)

I host a custom Fedora repository that you can use for automatic updates.

```bash
sudo dnf config-manager addrepo --from-repofile=https://jelmerro.nl/fedora/jelmerro.repo
sudo dnf install mp3_linter
```

## Contribute

You can support my work on [ko-fi](https://ko-fi.com/Jelmerro) or [Github sponsors](https://github.com/sponsors/Jelmerro).
Another way to help is to report issues or suggest new features.
Please try to follow recommendations by flake8 and pylint when developing.
For an example vimrc that can auto-format based on the included linters,
you can check out my personal [vimrc](https://github.com/Jelmerro/vimrc).

## Building

To create your own builds you can use [jfpm](https://github.com/Jelmerro/jfpm).
Please clone or download both this repo and jfpm, then run `../jfpm/release_py_deps.sh`.
This will build releases for various platforms and output them to `dist`.

## Usage

Basic usage: `mp3_linter <folder>`

This will scan all the MP3s in the specified folder for errors.
To automatically fix them, add `--fix`.
You can also exclude certain subfolders with `--exclude`, which can be repeated.

The checks are written to be consistent in finding tag errors,
but are opinionated for a fairly specific artist folder structure.
Issues for linting checks that you would like to change probably won't be accepted,
unless they are not working as intended and thus a bug.
This also extends to the fact that this linter is exclusively for MP3 files.

## Why & How

To ensure that ALL MP3 files follow the exact same structure for tagging.
This leads to consistency when playing them, searching for songs etc.
Files will also not be unnecessarily big due to redundant tags or large cover art.
This linter can automatically fix both of these scenarios and more.
While MP3 obviously does not support the lossless quality of for example FLAC,
this linter will report files that are not 320 Kbps CBR to strive for maximum quality.
It also makes sure to report improperly structured files when linting,
which it does by building a file path based on the tags and comparing it to disk.
This can also be automatically fixed, but only for files that do not have other errors.
There are also checks for duplicate tracks on a single disc, padded numbers,
missing total count, duplicate/missing/large/wrongly-encoded covert art,
folder structure for multi-disc albums etc.
