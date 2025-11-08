#!/usr/bin/env python3
import os
import shutil
import sys
import urllib.parse

INVALID_CHARS = ['"', "'", ':']
REPLACEMENT = '-'

def sanitize_name(name):
    new_name = name
    for c in INVALID_CHARS:
        new_name = new_name.replace(c, REPLACEMENT)
    return new_name

def confirm(prompt):
    choice = input(f"{prompt} [Y/n] ").strip().lower()
    if choice in ('', 'y', 'yes'):
        return True
    return False

def scan_directory(src_root):
    print(f"--- Scanning {src_root} ---\n")
    rename_map = {}
    skip_list = []

    for root, dirs, files in os.walk(src_root):
        for item in dirs + files:
            old_path = os.path.join(root, item)
            rel_path = os.path.relpath(old_path, src_root)
            new_name = sanitize_name(item)
            if new_name != item:
                new_rel = os.path.join(os.path.dirname(rel_path), new_name)
                prompt = f"Rename /{rel_path} to /{new_rel}"
                if confirm(prompt):
                    rename_map[rel_path] = new_rel
                else:
                    print(f"/{rel_path} will be skipped")
                    skip_list.append(rel_path)
    return rename_map, skip_list

def copy_directory(src_root, dst_root, rename_map, skip_list):
    print(f"\n--- Copying {src_root} to {dst_root} ---\n")

    # Convert smb:// URL to mount path (idk make sure this works later)
    if dst_root.startswith("smb://"):
        dst_root = os.path.join("/run/user/%d/gvfs" % os.getuid(), "smb-share:server=" + dst_root[6:].replace("/", ",share="))

    for root, dirs, files in os.walk(src_root):
        for item in dirs + files:
            rel_path = os.path.relpath(os.path.join(root, item), src_root)
            if rel_path in skip_list:
                continue

            dest_rel = rename_map.get(rel_path, rel_path)
            src_path = os.path.join(src_root, rel_path)
            dest_path = os.path.join(dst_root, dest_rel)

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)
            elif os.path.isdir(src_path):
                os.makedirs(dest_path, exist_ok=True)

def main():
    if len(sys.argv) != 3:
        print("Usage: smbcopy <source_dir> <smb_destination>")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]

    if not os.path.isdir(src):
        print(f"Error: {src} is not a valid directory")
        sys.exit(1)

    rename_map, skip_list = scan_directory(src)
    copy_directory(src, dst, rename_map, skip_list)

if __name__ == "__main__":
    main()
