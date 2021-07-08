⚠️ **Important:** This project has moved to GitLab. For the latest code, see: https://gitlab.com/reidrac/ubox-msx-lib

# ubox MSX lib

This is a set of libraries and tools to make MSX games using the C programming
language.

There are three main components:

  - **ubox**: thin wrapper around MSX 1 BIOS, focusing on Screen 2 and 32K
    cartridge ROMs.
  - **spman**: a simple sprite and pattern manager with flickering support.
  - **mplayer**: a wrapper around Arkos 2 AKM player, supporting music and
    priority based one channel sound effects.

The aim is making MSX games in C, without writing Z80 assembler or having a
deep knowledge of the system.

## Requirements

 - SDCC (3.9.0 recommended)
 - GNU Make (others may work)
 - a POSIX compatible environment

If you want to build the example you will also need:

 - python 3
 - pillow
 - GCC (only the C compiler)
 - Disark, one of the tools distributed with Arkos Tracker 2 (download from
   [Arkos Tracker 2 website](http://www.julien-nevo.com/arkostracker/))

On Windows 10, there are reports of successful builds using:

 - latest version of Cygwin64 with package for gcc-core 10.2.0-1
 - SDCC 4.0.0
 - python 3.9.1

If you want to build the docs you will also need:

 - pandoc
 - python 3
 - pygments
 - pandocfilters

## Building

To build the libraries run:

    make

After a successful build, the libraries should be in `./lib`.

The include files are ready to use in `./include`.

Add those directories in `SDCC`'s search path and you are ready to go.

Note: `make` is expected to be run from the root of the repo. The PATH env
variable will be set automatically.

### Building the example

An example game is included with the libraries and it can be built with:

    make game

After a successful build, the game ROM should be in `./bin`.

### Building the docs

The documentation is available at
[usebox.net](https://www.usebox.net/jjm/ubox-msx-lib/), so this is optional.

To build the docs run:

    make docs

The reference in `HTML` format will be generated in `./docs`.

## Contributing

All contributions are welcome.

If you think you have found a bug, please submit a bug report providing some
information:

 - What was expected to happen
 - What actually happens
 - How to reproduce the issue

Some advice if you want to make a successful contribution:

 - Be cordial
 - Get early feedback, specially when working on a large contribution
 - Contributions always require a pull request and a review

## Authors

This was mostly written by Juan J. Martinez during the development of
[Night Knight](https://www.usebox.net/jjm/night-knight/) and
[Uchūsen Gamma](https://www.usebox.net/jjm/uchusen-gamma/).

Other contributors:

 - Pedro de Medeiros
 - Your name here?

## Copying

This software is distributed under MIT license, unless stated otherwise.

See COPYING file.

**TL;DR**: the only condition is that you are required to preserve the copyright
and license notices. Licensed works, modifications, and larger works may be
distributed under different terms and without source code; this includes any game
made with the help of this software.

Credit is appreciated, but is not a legal requirement. For example: you can add
to the game's documentation a note like "This game uses ubox MSX lib".

There are some third party tools included here for convenience and are covered
by their own license or are public domain.

