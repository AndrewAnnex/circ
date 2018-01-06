Circ
====

*Making just ok CTX imager vrt mosaics since 2018*


Installation
------------

currently you must have gdal and `aria2c <https://aria2.github.io/>`__ installed and available in your PATH.
then download or clone the repo and then run `python setup.py install`


Usage
-----
```
Usage:       circ make-vrt MINX MINY MAXX MAXY [NAME] [EM_TOL] [DRY_RUN]
             circ make-vrt --minx MINX --miny MINY --maxx MAXX --maxy MAXY [--name NAME] [--em-tol EM_TOL] [--dry-run DRY_RUN]
```

specifify a minimum and maximum longitude (minx maxx) and a minimum and maximum latitude (miny maxy).

So to make a ctx mosaic around Gale Crater, after installation simply run:
```
circ make-vrt 136.0 -7.0 139.5 -3.5 --name gale

```
This will create a folder called `gale` in which a bunch of ctx images will be downloaded

The VRT image created at the end can then be used to construct downsampled images or even construct a merged image (which would take less disk space) using other gdal command line tools.

