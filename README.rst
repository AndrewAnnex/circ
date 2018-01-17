Circ
====

*Making just ok CTX mosaics since 2018*

Circ builds CTX mosaics by reading the CTX image metadata to select images that
intersect the bounding box the user provides, and then does some basic filtering and
stochastic image reduction to come up with a reasonably minimal list of images that cover the bbox
and have low-ish emission angles.

The images used come from ASU Mars Space Flight Facility viewer.mars.asu.edu.


Installation
------------

currently you must have gdal and wget installed and available in your PATH.
then download or clone the repo and then run `python setup.py install`


Usage
----- 
  
.. code:: bash

  Usage:       circ make-vrt MINX MINY MAXX MAXY [NAME] [EM_TOL] [DRY_RUN]
               circ make-vrt --minx MINX --miny MINY --maxx MAXX --maxy MAXY [--name NAME] [--em-tol EM_TOL] [--dry-run DRY_RUN]
   
  
Specify a minimum and maximum longitude (minx maxx) and a minimum and maximum latitude (miny maxy).
By default the maximum emission angle allowed is 5.0, but this can be reduced to lower values without
loosing much spatial coverage if any. Try using the `--dry-run` flag and different emission angle values to
observe how the count in images changes for your bbox.

So to make a ctx mosaic around Gale Crater, after installation simply run:

.. code:: bash

  circ make-vrt 136.0 -7.0 139.5 -3.5 --name gale --em_tol 1.0


This will create a folder called `gale` in which a bunch of ctx images will be downloaded. Also the emission angle tolerance has been lowered to 1.0 (less than or equal to)
The bbox passed in here is a bit larger than is truly needed, so some extra images will be downloaded.
If you are running this example it would be worth contracting it by a half to three quarters of a degree for each coordinate.

The VRT image created at the end can then be used directly in applications like QGIS or to construct a merged image (which would take less disk space) using other gdal command line tools like so:

.. code:: bash

  gdal_translate -co COMPRESS=JPEG -co TILED=YES -co COPY_SRC_OVERVIEWS=YES gale.vrt gale_jpeg.tif
  gdaladdo -r average --config COMPRESS_OVERVIEW JPEG --config JPEG_QUALITY_OVERVIEW 85 gale_jpeg.tif 2 4 8



To see that we actually saved space, here is the total space the gale folder takes:

.. code:: bash

  du -sh ./gale
  5.0G    ./gale


And this is the amount of space the final jpeg compressed tif version has:

.. code:: bash

  du -sh ./gale_jpeg.tif
  817M    ./gale


At this point you can delete the vrt and folder of tiffs to save disk space, and use other gdal commands to clip the mosaic to clip the mosaic to the bounding box.

