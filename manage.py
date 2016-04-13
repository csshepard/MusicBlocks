#!/usr/bin/env python
from migrate.versioning.shell import main

if __name__ == '__main__':
    main(url='sqlite:///MusicBlocks.db', debug='False', repository='sql_repo')
