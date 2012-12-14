import contextlib
import logging
import os
from datetime import datetime

from teuthology import misc as teuthology

log = logging.getLogger(__name__)

def task(ctx, config):
    """
    Setup MPI and execute commands

    Example that starts an MPI process on specific clients::

        tasks:
        - ceph:
        - ceph-fuse: [client.0, client.1]
        - mpi: 
            nodes: [client.0, client.1]
            exec: ior ...

    Example that starts MPI processes on all clients::

        tasks:
        - ceph:
        - ceph-fuse:
        - mpi:
            exec: ior ...

    Example that starts MPI processes on all roles::

        tasks:
        - ceph:
        - mpi:
            nodes: all
            exec: ...

    """
    assert isinstance(config, dict), 'task mpi got invalid config'
    assert 'exec' in config, 'task mpi got invalid config, missing exec'
    mpiexec = config['exec']
    hosts = []
    remotes = []
    master_remote = None
    if 'nodes' in config:
        if isinstance(config['nodes'], basestring) and config['nodes'] == 'all':
            for role in  teuthology.all_roles(ctx.cluster):
                (remote,) = ctx.cluster.only(role).remotes.iterkeys()
                hostname = remote.name.split('@')[1]
                hosts.append(hostname)
                remotes.append(remote)
            (master_remote,) = ctx.cluster.only(config['nodes'][0]).remotes.iterkeys()
        elif isinstance(config['nodes'], list):
            for role in config['nodes']:
                (remote,) = ctx.cluster.only(role).remotes.iterkeys()
                hostname = remote.name.split('@')[1]
                hosts.append(hostname)
                remotes.append(remote)
            (master_remote,) = ctx.cluster.only(config['nodes'][0]).remotes.iterkeys()
    else:
        roles = ['client.{id}'.format(id=id_) for id_ in teuthology.all_roles_of_type(ctx.cluster, 'client')]
        (master_remote,) = ctx.cluster.only(roles[0]).remotes.iterkeys()
        for role in roles:
            (remote,) = ctx.cluster.only(role).remotes.iterkeys()
            hostname = remote.name.split('@')[1]
            hosts.append(hostname)
            remotes.append(remote)

    log.info('mpi rank 0 is: {name}'.format(name=master_remote.name))

    # write out the mpi hosts file
    log.info('mpi nodes: [%s]' % (', '.join(hosts)))
    hostfiledata = '\n'.join(hosts) + '\n'
    teuthology.write_file(remote=master_remote, path='/tmp/cephtest/mpi-hosts', data='\n'.join(hosts))
    log.info('mpiexec on {name}: {cmd}'.format(name=master_remote.name, cmd=mpiexec))
    args=['mpiexec', '-f', '/tmp/cephtest/mpi-hosts']
    args.extend(mpiexec.split(' '))
    master_remote.run(args=args, )
    log.info('mpi task completed')

