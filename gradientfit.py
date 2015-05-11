import os
import argparse

import numpy as np
import scipy.misc
import scipy.ndimage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('--output', '-o', required=False)
    args = parser.parse_args()

    image = scipy.misc.imread(args.filename)
    print(image.shape)
    brightness = np.mean(image, axis=2)
    print(brightness.shape)

    # Model: z = ax + by + c
    # A z = b
    # Each row of A is (1, x-coordinate, y-coordinate)
    # Each entry of b is the corresponding brightness
    # Find the z that minimizes the sum of squared errors
    ys, xs = np.mgrid[0:image.shape[0], 0:image.shape[1]]
    xs = xs.ravel()
    ys = ys.ravel()
    brightness = brightness.ravel()
    ones = np.ones_like(xs)
    A = np.c_[ones, xs, ys]
    z, residuals, rank, s = np.linalg.lstsq(A, brightness)
    # print(z)
    print('Angle is %.4f radians' % (np.arctan2(-z[2], z[1]),))
    correction = np.dot(np.c_[xs, ys], [[z[1]], [z[2]]]).ravel()
    correction -= np.mean(correction)
    # brightness -= correction
    image -= correction.reshape(image.shape[0], image.shape[1], 1)
    if args.output is None:
        base, ext = os.path.splitext(args.filename)
        output = '%s-flat%s' % (base, ext)
    else:
        output = args.output
    scipy.misc.imsave(output, image.astype(np.uint8))


if __name__ == "__main__":
    main()
