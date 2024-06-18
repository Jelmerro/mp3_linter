mp3_linter
==========

Opinionated & consistent ID3 linter & fixer

## Features

- Scan an entire folder of MP3s for ID3 tag issues
- Fix issues automatically whenever possible: image resize, renaming and tag issues
- Reports errors in clear colorcoded entries per file, and summarizes the results
- See "Why & How" for an explanation of how the linter works

## Install

```bash
pip install --user -I git+https://github.com/Jelmerro/mp3_linter
```

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

## License

This project was made by [Jelmer van Arnhem](https://github.com/Jelmerro)
and can be copied under the terms of the MIT license, see the LICENSE file for details.
