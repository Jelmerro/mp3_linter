mp3_linter
==========

Opinionated & consistent ID3 linter & fixer

## Features

- Scan an entire folder of MP3s for ID3 tag issues
- Fix issues automatically whenever possible: image resize, renaming and tag issues
- Reports errors in clear colorcoded entries per file, and summarizes the results

## Usage

- (optional) Use a virtualenv: `python3 -m venv ENV` and `source ./ENV/bin/activate`
- Install requirements `pip install -r requirements.txt`
- Run with `python3 mp3_linter.py <folder>`

This will scan all the MP3s in the specified folder for errors.
To automatically fix them, add `--fix`.
You can also exclude certain subfolders with `--exclude`, which can be repeated.

The checks are written to be consistent in finding tag errors,
but are opinionated for a fairly specific artist folder structure.
Issues for linting checks that you would like to change probably won't be accepted,
unless they are not working as intended and thus a bug.
This also extends to the fact that this linter is exclusively for MP3 files.

## License

This project was made by [Jelmer van Arnhem](https://github.com/Jelmerro)
and can be copied under the terms of the MIT license, see the LICENSE file for details.
