#!/usr/bin/env python

import os
import shutil
import subprocess
import argparse
import json
import datetime
import logging

logging.basicConfig(level=logging.INFO)

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


def backup_world(world_name, world_dir, backup_dir):
    backup_name = "{}_{}".format(world_name, datetime.datetime.now().date().isoformat())
    backup_dest = os.path.join(backup_dir, backup_name)

    if (os.path.exists(world_dir) and not os.path.exists(backup_dest)):
        logging.info('backing up {} from {} to {}'.
            format(world_name, world_dir, backup_dir))
        shutil.copytree(world_dir, backup_dest)

    return backup_dest


def generate_map(world_dir, overview_dir):
    logging.info('generating overviewer map from {} in {}'.format(world_dir, overview_dir))
    subprocess.call('overviewer.py {} {}'.format(world_dir, overview_dir), shell=True)


def compress_backup(backup_dest):
    logging.info('compressing {}'.format(backup_dest))
    subprocess.call('zip -rq {} {}'.format(backup_dest + '.zip', backup_dest), shell=True)
    shutil.rmtree(backup_dest)


def prune_backups(backup_dir, max_backup_size):
    backups = list(reversed(sorted(os.listdir(backup_dir))))

    while(backups and directory_size(backup_dir) > max_backup_size):
        backup = backups.pop()
        logging.info('pruning {}'.format(backup))
        os.remove(os.path.join(backup_dir, backup))


def main():
    parser = argparse.ArgumentParser(description='Perform Minecraft server backup and generate overviewer maps.')
    parser.add_argument('-c', '--config', help='the location of the configuration to use', default="./config.json", required=False)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    for world_name, world_config in config.iteritems():
        backup_dest = backup_world(world_name, world_config['world_dir'], world_config['backup_dir'])
        generate_map(backup_dest, world_config['overview_dir'])
        compress_backup(backup_dest)
        prune_backups(world_config['backup_dir'], world_config['max_backup_size'])


if __name__ == '__main__':
    main()
