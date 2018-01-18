from setuptools import setup
import io

# some influences here came from https://github.com/audreyr/cookiecutter/blob/master/setup.py

version = '0.0.1'

with io.open('README.rst', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

setup(
    name     = 'circ',
    version  = version,
    packages = ['circ'],
    license  = 'MIT',
    description = 'A basic CLI to make mosaic vrts using ctx imagery',
    long_description = readme,
    # Author details
    author='Andrew Annex',
    author_email='annex@jhu.edu',
    url='https://github.com/andrewannex/circ',
    download_url='https://github.com/AndrewAnnex/circ/archive/0.0.1.tar.gz',

    install_requires=['requests', 'fire', 'moody', 'geopandas', 'shapely', 'deco', 'sh', 'tqdm'],

    entry_points={
        'console_scripts': [
            'circ = circ.circ:main'
        ]
    },

    include_package_data=True,

    package_data = {'': ['circ/data/mars_mro_ctx_edr_m_c0a/*.*'] },

    keywords=['mars', 'nasa', 'ode', 'pds', 'cli', 'tool', 'ctx', 'circ', 'mosaic', 'gdal'],

    classifiers=[
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: GIS'
    ]
)
