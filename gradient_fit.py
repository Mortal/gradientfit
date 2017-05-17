#!/usr/bin/env python2
# encoding: utf8

'''
Gimp plugin "Gradient fit"

Author:
Mathias Rav

License:

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

The GNU Public License is available at
http://www.gnu.org/copyleft/gpl.html
'''

from __future__ import print_function, unicode_literals, division
# from itertools import izip as zip

import numpy as np
import scipy.misc
# import scipy.ndimage

from gimpfu import _, gimp, main, PF_DRAWABLE, PF_IMAGE, register, pdb

import gettext
gettext.install('gimp20', gimp.locale_directory, unicode=True)


def python_fu_gradient_fit(img, drawable):
    img.undo_group_start()
    gimp.progress_init('Gradient fit')
    d = 3
    ATA = np.zeros((d, d))
    ATb = np.zeros((d, 1))
    tilerows = img.height // 64
    for i in range(tilerows+1):
        for j in range(10000):
            tile = drawable.get_tile(False, i, j)
            if tile is None:
                break
            assert tile.bpp == d
            tile_list = [tile[i_] for i_ in range(len(tile))]
            tile_array = np.array(tile_list).view(np.uint8).reshape((tile.eheight, tile.ewidth, 3))
            brightness = np.mean(tile_array, axis=2).reshape((tile.eheight*tile.ewidth, 1))
            ys, xs = np.mgrid[64*i:64*i+tile_array.shape[0], 64*j:64*j+tile_array.shape[1]]
            xs = xs.ravel()
            ys = ys.ravel()
            ones = np.ones_like(xs)
            A = np.c_[ones, xs, ys]
            ATA += np.dot(A.T, A)
            ATb += np.dot(A.T, brightness)
        gimp.progress_update(0.50*i/tilerows)
    z = np.dot(np.linalg.pinv(ATA), ATb)
    # print(z)
    # correction = np.dot(np.c_[xs, ys], [[z[1]], [z[2]]]).ravel()
    # correction -= np.mean(correction)
    width = img.width
    height = img.height
    mean_correction = (width * z[2, 0] * (height - 1) * height / 2 +
                       height * z[1, 0] * (width - 1) * width / 2) / (height * width)
    for i in range(tilerows+1):
        for j in range(10000):
            read_tile = drawable.get_tile(False, i, j)
            write_tile = drawable.get_tile(True, i, j)
            if read_tile is None:
                break
            assert read_tile.bpp == d
            tile_list = [read_tile[i_] for i_ in range(len(read_tile))]
            tile_array = np.array(tile_list).view(np.uint8).reshape((read_tile.eheight, read_tile.ewidth, 3))
            ys, xs = np.mgrid[64*i:64*i+tile_array.shape[0], 64*j:64*j+tile_array.shape[1]]
            xs = xs.ravel()
            ys = ys.ravel()
            correction = np.dot(np.c_[xs, ys], z[1:3])
            # print(correction.min(), correction.max(), correction.mean(), mean_correction, correction.dtype)
            correction -= mean_correction
            # print(correction.min(), correction.max(), correction.mean(), correction.dtype)
            correction = correction.reshape((read_tile.eheight, read_tile.ewidth, 1))
            tile_array = tile_array - correction
            # print(tile_array.min(), tile_array.max(), tile_array.mean(), tile_array.dtype)
            tile_array = np.clip(tile_array, 0, 255)
            tile_array = tile_array.astype(np.uint8)
            for k, v in enumerate(tile_array.view('|S3').ravel()):
                write_tile[k] = v
            write_tile.flush()
        gimp.progress_update(0.50+0.50*i/tilerows)
    drawable.merge_shadow()
    drawable.update(0, 0, drawable.width, drawable.height)
    drawable.flush()
    gimp.progress_update(1)
    img.undo_group_end()


if __name__ == '__main__':
    register(
        'python-fu-gradient-fit',  # Function name
        '',  # Blurb / description
        _('Gradient fit'),  # Help
        'Mathias Rav',  # Author
        '2017 Mathias Rav',  # Copyright notice
        '2017 Jan 29',  # Date
        _('Gradient fit'),  # Menu label
        'RGB*,GRAY*',
        [
            (PF_IMAGE,    'img',      _('Input image'),    None),
            (PF_DRAWABLE, 'drawable', _('Input drawable'), None),
        ],
        [],  # No results
        python_fu_gradient_fit,  # Internal function name
        menu='<Image>/Filters/Distorts',  # Register in menu
        domain=('gimp20-template', gimp.locale_directory),
    )

    main()
