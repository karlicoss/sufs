[sufs](https://github.com/karlicoss/sufs) is a tool for 'merging' multiple directories into one via symlinks.

I'm syncing most of my stuff via syncthing, but some of it has to be locally (mainly for stupid reasons like massive `node_modules`
directory etc.). But it's nice to have a unified view of them so you don't have to memorize what did you put where.

Usage example:

```
   # initialize merged dir`
   mkdir /home/user/datas 

   # you might want to keep the following in cron
   sufs.py --to /home/user/datas /home/user/syncthing/data /home/user/dropbox/data /home/user/syncthing/data
```

Before I wrote this script I tried FUSE based filesystems: [Unionfs](https://en.wikipedia.org/wiki/UnionFS) and [Mergerfs](https://github.com/trapexit/mergerfs), but wasn't really satisfied. Weirdly, couldn't also find anythig existing on github, so had to write my own.

First, you don't know where actually fuse mounted dirst reside. Second, for instance, mergerfs had some weird new file handling logic, so the directories would end up scattered across multiple sources. Overall I found it a bit confusing.

This script uses symlinks, so you always know the actual location; and also maintains the top level directory as read only, so you can't end up with dangling directories.

The only disadvantage at the moment is that symlink updating can only happen once a minute if you run via cron, but should be easy to use inotify if that's an issue.
