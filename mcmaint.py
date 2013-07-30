#!/usr/bin/env python

import os
import shutil
import subprocess
import argparse
import json
import datetime


def directory_size(path):
    total_size = 0
    seen = set()

    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)

            try:
                stat = os.stat(fp)
            except OSError:
                continue

            if stat.st_ino in seen:
                continue

            seen.add(stat.st_ino)

            total_size += stat.st_size

    return total_size / 1000000.0  # return in mb


def prune_backups(backup_dir, max_backup_size):
    backups = list(reversed(sorted(os.listdir(backup_dir))))
    print(backups)

    while(backups and directory_size(backup_dir) > max_backup_size):
        backup = backups.pop()
        os.remove(os.path.join(backup_dir, backup))


def backup_world(server_dir, world_name, backup_dir):
    world_dir = os.path.join(server_dir, world_name)
    backup_name = "{}_{}".format(world_name, datetime.datetime.now().date().isoformat())
    backup_dest = os.path.join(backup_dir, backup_name)

    if (os.path.exists(world_dir) and not os.path.exists(backup_dest)):
        shutil.copytree(world_dir, backup_dest)

    return backup_dest


def generate_map(world_dir, overviewer_dir):
    subprocess.call('overviewer.py {} {}'.format(world_dir, overviewer_dir), shell=True)


def compress_backup(backup_name, backup_dest):
    subprocess.call('zip -r {} {}'.format(backup_dest + '.zip', backup_dest), shell=True)
    shutil.rmtree(backup_dest)


def main():
    parser = argparse.ArgumentParser(description='Perform Minecraft server backup and generate overviewer maps.')
    parser.add_argument('-c', '--config', help='the location of the configuration to use', default="./config.json", required=False)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    backup_dest = backup_world(cfg['server_dir'], cfg['world_name'], cfg['backup_dir'])
    generate_map(backup_dest, cfg['overviewer_dir'])
    compress_backup(backup_dest)
    prune_backups(cfg['backup_dir'], cfg['max_backup_size'])


if __name__ == '__main__':
    main()
