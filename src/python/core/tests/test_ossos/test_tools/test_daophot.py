__author__ = "David Rusk <drusk@uvic.ca>"

import unittest

from tests.base_tests import FileReadingTestCase
from ossos import daophot

DELTA = 0.0001


class DaophotTest(FileReadingTestCase):
    def test_phot(self):
        """
        Test data to compare with generated by running make testphot
        which runs the equivalent Perl script with the same data.
        """
        fits_filename = self.get_abs_path("data/1616681p22.fits")
        x_in = 560.06
        y_in = 406.51
        ap = 4
        insky = 11
        outsky = 15
        maxcount = 30000.0
        exptime = 1.0

        swidth = outsky - insky
        apcor = 0.0

        hdu = daophot.phot(fits_filename, x_in, y_in, aperture=ap, sky=insky,
                           swidth=swidth, apcor=apcor, maxcount=maxcount,
                           exptime=exptime)

        def get_first(param):
            value_list = hdu[param]
            self.assertEqual(len(value_list), 1)
            return value_list[0]

        xcen = get_first("XCENTER")
        ycen = get_first("YCENTER")
        mag = get_first("MAG")
        magerr = get_first("MERR")

        self.assertAlmostEqual(xcen, 560.0, 1)
        self.assertAlmostEqual(ycen, 406.6, 1)
        self.assertAlmostEqual(mag, 24.64, 2)
        self.assertAlmostEqual(magerr, 0.223, 2)

    def test_phot_mag(self):
        fits_filename = self.get_abs_path("data/1616681p22.fits")
        x_in = 560.06
        y_in = 406.51
        ap = 4
        insky = 11
        outsky = 15
        maxcount = 30000.0
        exptime = 1.0

        swidth = outsky - insky
        apcor = 0.0

        x, y, mag, magerr = daophot.phot_mag(fits_filename, x_in, y_in,
                                             aperture=ap, sky=insky,
                                             swidth=swidth, apcor=apcor,
                                             maxcount=maxcount,
                                             exptime=exptime)

        assert_that(x, close_to(560.000, DELTA))
        assert_that(y, close_to(406.600, DELTA))
        assert_that(mag, close_to(24.769, DELTA))
        # NOTE: minor difference in magnitude error: 0.290 vs 0.291
        assert_that(magerr, close_to(0.290, 0.0011))


if __name__ == '__main__':
    unittest.main()