# libdvdread

**libdvdread** is a cross-platform library for simple navigation of DVDs.

It supports multimedia DVDs: DVD-Video and DVD-Audio.

It's been in use for more than 20 years to support any time of Disc.

## Goals and features

It focuses on DVD-Video and DVD-Audio; it does not support DVD menus, but
provides the low-level access to those discs and the DVD structures.

Written in C, cross-platform, it gives low-level access to DVD structures.

It works well in conjunction with ***libdvdnav*** *(menus)* and ***libdvdcss*** *(cipher)*.

## Where does it come from?

This library is based on a lot of code and expertise from the **Ogle project**.
**Ogle** was the first DVD player who implemented **free DVD navigation**. The
**libdvdread** developers wish to express their gratitude to the Ogle people
for all the valuable research work they have done.

Initially, the dvdnav code was part of a plugin to the xine media player
called xine-dvdnav. Later on, the DVD VM specific code was split
from xine-dvdnav and went into the first version of libdvdnav.

Then, it was forked, and forked again on MPlayer repositories.
libdvdnav and libdvdread were merged, and then split again.

## Where is it now?

Libdvdread is hosted [here](https://code.videolan.org/videolan/libdvdread).

Libdvdnav is hosted [here](https://code.videolan.org/videolan/libdvdnav).

You can find more information [here](https://www.videolan.org/developers/libdvdnav.html)

Please report bugs to the developers mailinglist at
[dvdnav mailing list](https://mailman.videolan.org/listinfo/libdvdnav-devel)

## License

**Libdvdread** is completely licensed under GPLv2/v3. You may use it at wish within the
bounds of this license. See the file [COPYING](https://code.videolan.org/videolan/libdvdread/-/blob/master/COPYING) for a copy of the GPL.

## Using libdvdread

A detailed description of DVD structures is available [here](http://www.mpucoder.com/dvd/)

All documentation is also accessible [here](http://dvdnav.mplayerhq.hu/#docs)

## Deciphering disks

**Libdvdread** does not do any decryption of the CSS algorithm. This task can be delegated to **libdvdcss**.

Install *libdvdcss* from source or from your distribution (*libdvd-pkg*) to play full DVDs,
if your country allows this to work legally.

Note that *libdvdnav* is useful for interactive DVD menus.

## CoC

The [VideoLAN Code of Conduct](https://wiki.videolan.org/Code_of_Conduct/) applies to this project.

# Compile

1. Install [Meson](https://mesonbuild.com/) (0.60 or higher), [Ninja](https://ninja-build.org/)
2. Run `mkdir build && cd build` to create a build directory and enter it
3. Run `meson setup ..` to configure meson, add `--default-library=static` if static linking is desired
4. Run `ninja` to compile

