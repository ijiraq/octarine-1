__author__ = "David Rusk <drusk@uvic.ca>"

import os
import re
import tempfile

from pyraf import iraf


class TaskError(Exception):
    """Base task error"""


def phot(fitsimage, x_in, y_in, aperture=15, sky=20, swidth=10, apcor=0.3,
         maxcount=30000.0, exptime=1.0):
    """Compute the centroids and magnitudes of a bunch sources detected on CFHT-MEGAPRIME images.

    Returns a MOPfiles data structure."""

    hdulist_in = fitsimage.as_hdulist()

    ## get the filter for this image
    filter = hdulist_in[0].header.get('FILTER', 'DEFAULT')

    ### Some CFHT zeropoints that might be useful
    zeropoints = {"I": 25.77,
                  "R": 26.07,
                  "V": 26.07,
                  "B": 25.92,
                  "DEFAULT": 26.0,
                  "g.MP9401": 26.4
    }

    ### load the
    if not filter in zeropoints:
        filter = "DEFAULT"

    zmag = hdulist_in[0].header.get('PHOTZP', zeropoints[filter])

    ### setup IRAF to do the magnitude/centroid measurements
    iraf.set(uparm="./")
    iraf.digiphot()
    iraf.apphot()
    iraf.daophot()

    ### check for the magical 'zeropoint.used' file
    zpu_file = "zeropoint.used"
    if os.access(zpu_file, os.R_OK):
        with open(zpu_file) as zpu_fh:
            zmag = float(zpu_fh.read())

    iraf.photpars.apertures = int(aperture)
    iraf.photpars.zmag = zmag
    iraf.datapars.datamin = 0
    iraf.datapars.datamax = maxcount
    #iraf.datapars.exposur="EXPTIME"
    iraf.datapars.exposur = ""
    iraf.datapars.itime = exptime
    iraf.fitskypars.annulus = sky
    iraf.fitskypars.dannulus = swidth
    iraf.centerpars.calgori = "centroid"
    iraf.centerpars.cbox = 5.
    iraf.centerpars.cthreshold = 0.
    iraf.centerpars.maxshift = 2.
    iraf.centerpars.clean = 'no'
    iraf.phot.update = 'no'
    iraf.phot.verbose = 'no'
    iraf.phot.verify = 'no'
    iraf.phot.interactive = 'no'

    # Used for passing the input coordinates
    coofile = tempfile.NamedTemporaryFile(suffix=".coo", delete=False)
    coofile.write("%f %f \n" % (x_in, y_in))

    # Used for receiving the results of the task
    # mag_fd, mag_path = tempfile.mkstemp(suffix=".mag")
    magfile = tempfile.NamedTemporaryFile(suffix=".mag", delete=False)

    # Close the temp files before sending to IRAF due to docstring:
    # "Whether the name can be used to open the file a second time, while
    # the named temporary file is still open, varies across platforms"
    coofile.close()
    magfile.close()

    iraf.phot(fitsimage.as_file().name, coofile.name, magfile.name)
    pdump_out = iraf.pdump(magfile.name, "XCENTER,YCENTER,MAG,MERR,ID,XSHIFT,YSHIFT,LID",
                           "MERR < 0.4 && MERR != INDEF && MAG != INDEF && PIER==0", header='no', parameters='yes',
                           Stdout=1)

    os.remove(coofile.name)
    os.remove(magfile.name)

    ### setup the mop output file structure
    hdu = {}
    hdu['header'] = {'image': hdulist_in,
                     'aper': aperture,
                     's_aper': sky,
                     'd_s_aper': swidth,
                     'aper_cor': apcor,
                     'zeropoint': zmag}
    hdu['order'] = ['X', 'Y', 'MAG', 'MERR', 'ID', 'XSHIFT', 'YSHIFT', 'LID']
    hdu['format'] = {'X': '%10.2f',
                     'Y': '%10.2f',
                     'MAG': '%10.2f',
                     'MERR': '%10.2f',
                     'ID': '%8d',
                     'XSHIFT': '%10.2f',
                     'YSHIFT': '%10.2f',
                     'LID': '%8d'}
    hdu['data'] = {}
    for col in hdu['order']:
        hdu['data'][col] = []

    for line in pdump_out:
        values = line.split()
        for col in hdu['order']:
            if re.match('\%.*f', hdu['format'][col]):
                if col == 'MAG':
                    values[0] = float(values[0]) - float(apcor)
                hdu['data'][col].append(float(values.pop(0)))
            elif re.match('\%.*d', hdu['format'][col]):
                hdu['data'][col].append(int(values.pop(0)))
            else:
                hdu['data'][col].append(values.pop(0))

    # Clean up temporary files generated by IRAF
    os.remove("datistabe.par")
    os.remove("datpdump.par")

    return hdu


def phot_mag(*args, **kwargs):
    """Wrapper around phot which only returns the computed magnitude directly."""
    hdu = phot(*args, **kwargs)
    return hdu["data"]["MAG"][0]