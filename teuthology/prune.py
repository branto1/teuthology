import logging
import os
import time

import teuthology

log = logging.getLogger(__name__)


# If we see this in any directory, we do not prune it
PRESERVE_FILE = '.preserve'


def main(args):
    verbose = args['--verbose']
    if verbose:
        teuthology.log.setLevel(logging.DEBUG)
    archive_dir = args['--archive']
    dry_run = args['--dry-run']
    pass_days = int(args['--pass'])
    remotes_days = int(args['--remotes'])

    prune_archive(archive_dir, pass_days, remotes_days, dry_run)


def prune_archive(archive_dir, pass_days, remotes_days, dry_run=False):
    max_days = max(pass_days, remotes_days)
    run_dirs = list()
    log.debug("Archive {archive} has {count} children".format(
        archive=archive_dir, count=len(os.listdir(archive_dir))))
    for child in os.listdir(archive_dir):
        item = os.path.join(archive_dir, child)
        if os.path.isdir(item) and is_old_enough(item, max_days):
            log.debug("Going to process %s ..." % item)
            run_dirs.append(item)
    for run_dir in run_dirs:
        log.debug("Processing %s ..." % run_dir)
        maybe_remove_passes(run_dir, pass_days, dry_run)
        maybe_remove_remotes(run_dir, remotes_days, dry_run)


def preserve(dir_name):
    preserve_path = os.path.join(dir_name, PRESERVE_FILE)
    if os.path.isdir(dir_name) and os.path.exists(preserve_path):
        return True
    return False


def is_old_enough(file_name, days):
    now = time.time()
    secs_to_days = lambda s: s / (60 * 60 * 24)
    age = now - os.path.getmtime(file_name)
    if secs_to_days(age) > days:
        return True
    return False


def maybe_remove_passes(run_dir, days, dry_run=False):
    contents = os.listdir(run_dir)
    if PRESERVE_FILE in contents:
        return
    for child in contents:
        item = os.path.join(run_dir, child)
        # Has this been marked for preservation?
        if preserve(item):
            continue
        # Is this a directory?
        if not os.path.isdir(item):
            continue
        # Is it old enough?
        if not is_old_enough(item, days):
            continue
        # Is it a job dir?
        summary_path = os.path.join(item, 'summary.yaml')
        if not os.path.exists(summary_path):
            continue
        # Is it a passed job?
        summary_lines = [line.strip() for line in
                         file(summary_path).readlines()]
        if 'success: true' in summary_lines:
            log.info("{job} is a {days}-day old passed job; removing".format(
                job=item, days=days))
            if not dry_run:
                pass
            # REMOVE


def maybe_remove_remotes(run_dir, days, dry_run=False):
    contents = os.listdir(run_dir)
    if PRESERVE_FILE in contents:
        return
    for child in contents:
        item = os.path.join(run_dir, child)
        # Has this been marked for preservation?
        if preserve(item):
            continue
        # Is this a directory?
        if not os.path.isdir(item):
            continue
        # Is it old enough?
        if not is_old_enough(item, days):
            continue
        # Does it have a remote subdir?
        remote_path = os.path.join(item, 'remote')
        if not os.path.isdir(remote_path):
            continue
        log.info("{job} is {days} days old; removing remote logs".format(
            job=item, days=days))
        # REMOVE
