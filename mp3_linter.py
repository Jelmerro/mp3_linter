import argparse
import glob
import os
import re
import shutil
import warnings
from PIL import Image

import stagger
warnings.filterwarnings("ignore")

SONG_FIELDS = set(["TIT2", "TPE1", "APIC", "TYER"])
ALBUM_SONG_FIELDS = set([
    "TIT2", "TPE1", "APIC", "TYER", "TRCK", "TALB", "TPOS"
])
TEXT_FIELDS = ["TALB", "TYER", "TIT2", "TPE1"]
COLORS = {
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "purple": "\x1b[35m"
}
END = "\x1b[0m"
APPNAME = os.path.basename(__file__.replace(".py", ""))


def walk_and_remove_empty(folder):
    work_dir = str(folder)
    success = True
    while success:
        try:
            work_dir = os.path.dirname(work_dir)
            os.rmdir(work_dir)
        except OSError:
            success = False


def cprint(text, color=None, end="\n"):
    if not color or color not in COLORS:
        print(text, end=end)
        return
    print(f"{COLORS[color]}{text}{END}", end=end)


def album_checks(tag, fix):
    issues = []
    fixable = []
    disc_track_fields = {"TRCK": "track", "TPOS": "disc"}
    for field in tag.values():
        if field.__dict__["frameid"] in disc_track_fields:
            if len(field.__dict__["text"]) != 1:
                fixable.append("Multiple {} number values".format(
                    disc_track_fields[field.__dict__["frameid"]]))
                if fix:
                    tag[field.__dict__["frameid"]] = field. \
                        __dict__["text"][0]
                    tag.write()
            if field.__dict__["text"][0].startswith("0"):
                fixable.append("Zero padded {} number".format(
                    disc_track_fields[field.__dict__["frameid"]]))
                if fix:
                    tag[field.__dict__["frameid"]] = field. \
                        __dict__["text"][0].replace("0", "", 1)
            if "/" not in field.__dict__["text"][0]:
                issues.append("No total {} specified".format(
                    disc_track_fields[field.__dict__["frameid"]]))
    return tag, issues, fixable


def cover_art_checks(tag, fix):
    issues = []
    fixable = []
    # Check if there is a single front cover and report differences
    all_covers = [
        field for field in tag.values() if field.__dict__["frameid"] == "APIC"
    ]
    front_covers = [
        img for img in all_covers if img.__dict__["type"] == 3
    ]
    relevant_covers = front_covers
    if not front_covers and all_covers:
        relevant_covers = all_covers
    if not all_covers:
        issues.append("No cover art found")
    if len(all_covers) > 1:
        if len(front_covers) > 1:
            fixable.append("Multiple front cover pictures found")
        elif front_covers:
            fixable.append("Single front cover, but also other images present")
        else:
            issues.append("Multiple embedded images found, none of them front")
    # Check the relevant covers for more specific errors
    for img in relevant_covers:
        if not img.__dict__["data"]:
            issues.append("Cover picture data is empty")
        if len(img.__dict__["data"]) > 1000000:
            fixable.append("Cover picture is too large >1MB")
        if img.__dict__["desc"]:
            fixable.append("Cover picture has a description")
        if img.__dict__["type"] != 3:
            fixable.append("Cover picture type is not Front")
        if img.__dict__["encoding"] != 0:
            issues.append("Cover picture has an incorrect encoding")
        if img.__dict__["mime"] not in ["image/jpeg", "image/png"]:
            fixable.append("Cover picture has an incorrect mime type")
    if not front_covers and len(all_covers) > 1:
        issues.extend(fixable)
        fixable = []
    if fixable and fix:
        new_cover = all_covers[0]
        if front_covers:
            new_cover = front_covers[0]
        mime_type = new_cover.__dict__["mime"].split("/")[1]
        too_big = len(new_cover.__dict__["data"]) > 1000000
        temp_file = f"/tmp/{APPNAME}_original.{mime_type}"
        with open(temp_file, "wb") as f:
            f.write(new_cover.__dict__["data"])
        if mime_type not in ["image/jpeg", "image/png"] or too_big:
            with Image.open(temp_file) as img:
                temp_file = f"/tmp/{APPNAME}.jpg"
                if too_big:
                    img = img.resize((700, 700), resample=Image.LANCZOS)
                if img.mode in ["RGBA", "P"]:
                    img = img.convert("RGB")
                img.save(temp_file, 'jpeg', quality=95)
        tag.picture = temp_file
        tag[stagger.id3.APIC][0].type = 3
        tag[stagger.id3.APIC][0].desc = ""
    return tag, issues, fixable


def collection_filename(mp3, tag, level, depth):
    # Collections that are prefixed with "!" follow different rules
    # - If it's a top-level collection the regular naming rules are followed
    # - The release year is not part of the album name for 1st and 2nd levels
    # - Third level onwards all regular naming rules are followed
    # Collections are never checked to have the correct base artist folder,
    # as that is usually the main difference compared to artist folders.
    artist = tag.artist.replace("/", "|")
    title = tag.title.replace("/", "|")
    album = tag.album.replace("/", "|")
    expected = f"{artist} - {title}.mp3"
    if level == 0:
        depth -= 1
    if getattr(tag, "album"):
        if level:
            if level > depth:
                expected = f"[{tag.date}] {album}/"
            elif album.startswith("The "):
                expected = album.replace("The ", "", 1) + "/"
            else:
                expected = f"{album}/"
        else:
            expected = ""
        if getattr(tag, "disc_total") > 1 and level:
            expected += f"CD{tag.disc}/"
        expected += f"{str(tag.track).zfill(2)} - {title}.mp3"
    base = mp3
    depth = depth or 1
    for _ in range(0, depth):
        base = re.sub(r"\/[^/]*$", "", base)
    expected = os.path.join(base, expected)
    if expected != mp3:
        return expected
    return None


def filesystem_checks(siblings, mp3, tag):
    issues = []
    # Check for the correct amount of tracks in the folder
    total_tracks = getattr(tag, "track_total")
    if getattr(tag, "album") and total_tracks:
        if len(siblings) != total_tracks:
            issues.append(
                f"Found {len(siblings)} files in folder, but"
                f" expected {total_tracks} tracks")
    # Check if it's the only file with this track number
    current_track = f"{str(getattr(tag, 'track')).zfill(2)} - "
    tracks_with_current_number = len([
        s for s in siblings if os.path.basename(s).startswith(current_track)
    ])
    if getattr(tag, "album") and tracks_with_current_number != 1:
        issues.append(
            f"Found {tracks_with_current_number} tracks with "
            "current track number, but expected exactly 1")
    # Check for filename
    artist = tag.artist.replace("/", "|")
    title = tag.title.replace("/", "|")
    album = tag.album.replace("/", "|")
    expected = f"{artist} - {title}.mp3"
    folder_count = 1
    if getattr(tag, "album"):
        expected = f"[{tag.date}] {album}/"
        folder_count = 2
        if getattr(tag, "disc_total") > 1:
            folder_count += 1
            expected += f"CD{tag.disc}/"
        expected += f"{str(tag.track).zfill(2)} - {title}.mp3"
    artist_path = mp3
    for _ in range(0, folder_count):
        artist_path = re.sub(r"\/[^/]*$", "", artist_path)
    # Check for collection and return special filename
    base_dir = os.path.dirname(mp3)
    for level in range(0, 7):
        if os.path.basename(base_dir).startswith("!"):
            return issues, collection_filename(mp3, tag, level, folder_count)
        base_dir = os.path.dirname(base_dir)
    # Return expected filename and check for incorrect artist folder
    expected = os.path.join(artist_path, expected)
    fol = os.path.basename(artist_path)
    if fol.lower() not in artist.lower() and fol.lower() not in title.lower():
        issues.append(
            "File might not be stored in the right artist folder:\n"
            f"    folder:  {fol}\n    artist:  {artist}\n    title:   {title}")
    if mp3 == expected:
        return issues, None
    return issues, expected


def run_checks(siblings, mp3, tag, fix=False):
    issues = []
    fixable = []
    fields = set()
    # Incorrect ID3 tag version
    if tag.version != 3:
        issues.append(f"Incorrect tag version {tag.version}")
    # Album specific checks
    if getattr(tag, "album"):
        tag, album_issues, album_fixable = album_checks(tag, fix)
        issues.extend(album_issues)
        fixable.extend(album_fixable)
    # Cover art checks
    tag, cover_issues, cover_fixable = cover_art_checks(tag, fix)
    issues.extend(cover_issues)
    fixable.extend(cover_fixable)
    # Check for an incorrect amount of values and keep a list of present fields
    for field in tag.values():
        fields.add(field.__dict__["frameid"])
        if field.__dict__["frameid"] in TEXT_FIELDS:
            if field.__dict__["frameid"] == "TALB" and getattr(tag, "album"):
                if not field.__dict__["text"]:
                    issues.append("Empty value set for {}".format(
                        TEXT_FIELDS[field.__dict__["frameid"]]))
                if len(field.__dict__["text"]) > 1:
                    issues.append("Multiple values for {}".format(
                        TEXT_FIELDS[field.__dict__["frameid"]]))
    # Compare fields that are present compared to the expected set of fields
    incorrect = SONG_FIELDS ^ fields
    missing = SONG_FIELDS & incorrect
    redundant = incorrect - SONG_FIELDS
    if getattr(tag, "album"):
        incorrect = ALBUM_SONG_FIELDS ^ fields
        missing = ALBUM_SONG_FIELDS & incorrect
        redundant = incorrect - ALBUM_SONG_FIELDS
    for miss in missing:
        issues.append(f"Missing required {miss} field")
    for red in redundant:
        fixable.append(f"Redundant field {red} present")
        if fix:
            for field in redundant:
                if field in tag:
                    del tag[field]
    # Checks for the file location and being stored next to the right files
    fs_issues, filename = filesystem_checks(siblings, mp3, tag)
    issues.extend(fs_issues)
    # Write fixes to file, return the list of issues and the number of fixes
    if fixable and fix:
        tag.write()
    return issues, fixable, filename


def main(folder, exclusions, fix=False):
    files = sorted(glob.glob("{}**/*.mp3".format(folder), recursive=True))
    for exc in exclusions:
        files = [f for f in files if not f.startswith(os.path.abspath(exc))]
    total_files = len(files)
    total_unreadable = 0
    total_issues = 0
    total_fixable = 0
    unsafe_file_moves = 0
    safe_file_moves = 0
    for mp3 in files:
        try:
            tag = stagger.read_tag(mp3)
        except (stagger.errors.NoTagError, FileNotFoundError):
            cprint(mp3, "blue")
            cprint("  - Failed to read ID3 tag\n", "red")
            total_unreadable += 1
            continue
        siblings = [
            f for f in files if os.path.dirname(f) == os.path.dirname(mp3)
        ]
        issues, fixable, new_location = run_checks(siblings, mp3, tag, fix)
        if new_location:
            if issues:
                unsafe_file_moves += 1
            else:
                safe_file_moves += 1
            if fix and not issues:
                os.makedirs(os.path.dirname(new_location), exist_ok=True)
                shutil.move(mp3, new_location)
                walk_and_remove_empty(mp3)
                cprint("previously ", "green", "")
                cprint(mp3, "blue")
                cprint("moved to   ", "green", "")
                cprint(new_location, "purple")
            else:
                cprint("currently ", "green" if not issues else "yellow", "")
                cprint(mp3, "blue")
                cprint("should be ", "green" if not issues else "yellow", "")
                cprint(new_location, "purple")
        if not new_location and (issues or fixable):
            cprint(mp3, "blue")
        if issues:
            for issue in issues:
                cprint(f"  - {issue}", "yellow")
        if fixable:
            for f in fixable:
                cprint(f"  - {f}", "green")
        if new_location or issues or fixable:
            print("\n")
        total_issues += len(issues)
        total_fixable += len(fixable)
    grand_total = total_issues + total_fixable + total_unreadable
    grand_total += safe_file_moves + unsafe_file_moves
    if grand_total:
        cprint(
            f"Processed {total_files} files with {grand_total} total issues",
            "blue")
    else:
        cprint(
            f"Processed {total_files} files that are all named and "
            "tagged correctly", "green")
    if total_unreadable:
        cprint(f"- There are {total_unreadable} files unreadable", "red")
    if total_issues:
        cprint(
            f"- There are {total_issues} tag issues with manual work",
            "yellow")
    if fix:
        if total_fixable:
            cprint(
                f"- There were {total_fixable} tag issues fixed automatically",
                "green")
        if unsafe_file_moves:
            cprint(
                f"- There were {unsafe_file_moves} files "
                "that were not renamed, due to incomplete tags", "purple")
        if safe_file_moves:
            cprint(
                f"- There were {safe_file_moves} files renamed on disk",
                "purple")
    else:
        if total_fixable:
            cprint(
                f"- There are {total_fixable} issues fixable with the "
                "`--fix` argument", "green")
        if unsafe_file_moves:
            cprint(
                f"- There are {unsafe_file_moves} files "
                "that cannot moved, due to incomplete tags", "purple")
        if safe_file_moves:
            cprint(
                f"- There are {safe_file_moves} files that can be moved "
                "with `--fix` automatically", "purple")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Opinionated/consistent ID3 linter & fixer using stagger")
    parser.add_argument("folder", help="Folder to search for mp3 files")
    parser.add_argument(
        "--exclude", nargs="+", help="Folders to ignore when linting/fixing")
    parser.add_argument(
        "--fix", action="store_true",
        help="Automatically fix all the fixable issues and rename the files")
    args = parser.parse_args()
    main(args.folder, args.exclude or [], args.fix)
