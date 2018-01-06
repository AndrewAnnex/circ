import fire
import moody.moody as moody
import os
from pathlib import Path
import geopandas as gpd
from sh import mkdir, wget, Command
from deco import *
import shapely.geometry

here = Path(os.path.realpath(__file__)).parent


@concurrent
def _download(path, url, i, h):
    name = url.split('/')[-1]
    wget('-O', f'{path}/{name}', url, '--continue', '-q', '--show-progress', _fg=True)
    print(f'\nCompleted {name}, {i+1}/{h}')

@synchronized
def _download_all(path, urls):
    how_many = len(urls)
    for i, url in enumerate(urls):
        _download(path, url, i, how_many)


class Circ(object):

    def __init__(self, https=False):
        self._https = https
        self._ctx_shp = str(here / 'data' / 'mars_mro_ctx_edr_m_c0a' / 'mars_mro_ctx_edr_m_c0a.shp')
        self._gdalbuildvrt = Command('gdalbuildvrt')

    @property
    def _ode(self):
        return moody.ODE(https=self._https)

    @staticmethod
    def _reduce(data: gpd.GeoDataFrame)-> gpd.GeoDataFrame:
        tot_shape = None
        collection = []
        for c in data.itertuples():
            if tot_shape is None:
                tot_shape = shapely.geometry.Polygon(c.geometry)
                collection.append(c)
            else:
                intersection = tot_shape.intersection(c.geometry)
                if intersection.area / c.geometry.area <= .99:
                    tot_shape = tot_shape.union(c.geometry)
                    collection.append(c)

        return gpd.GeoDataFrame(collection)

    @staticmethod
    def _shuffle_reduce(data: gpd.GeoDataFrame)-> gpd.GeoDataFrame:
        tot_shape = None
        collection = []
        for c in data.sample(frac=1).itertuples():
            if tot_shape is None:
                tot_shape = shapely.geometry.Polygon(c.geometry)
                collection.append(c)
            else:
                intersection = tot_shape.intersection(c.geometry)
                if intersection.area / c.geometry.area <= .99:
                    tot_shape = tot_shape.union(c.geometry)
                    collection.append(c)

        return gpd.GeoDataFrame(collection)

    def get_asu_url(self, pid: str)-> str:
        index = self._ode.get_ctx_meta_by_key(pid, 'LabelURL')
        mrox = index.split('/')[-3]
        url = f'http://image.mars.asu.edu/stream/{pid}.tiff?image=/mars/images/ctx/{mrox}/prj_full/{pid}.tiff'
        return url

    def select_imgs(self, minx, miny, maxx, maxy, em_tol=10.0, num_iters=25)-> gpd.GeoDataFrame:
        query_res = gpd.GeoDataFrame(gpd.read_file(self._ctx_shp).cx[minx:maxx, miny:maxy])
        query_res['area'] = query_res.area
        query_res = self._reduce(query_res[query_res['EmAngle'] <= em_tol].sort_values(['EmAngle', 'area'], ascending=[True, False]))
        query_res = self._reduce(query_res.sort_values('area', ascending=False))
        # simplistic way to reduce number of images,
        # yes, I know using a tree would be better but whatevs
        for i in range(num_iters):
            query_res = self._shuffle_reduce(query_res)

        return query_res

    def get_urls(self, minx, miny, maxx, maxy, em_tol=10.0)-> gpd.GeoDataFrame:
        res = self.select_imgs(minx, miny, maxx, maxy, em_tol)
        res['url'] = [self.get_asu_url(pid) for pid in res['ProductId']]
        return res

    def make_vrt(self, minx, miny, maxx, maxy, name='mosaic', em_tol=10.0, dry_run=False):
        """
        Search for, then downloads all ctx images within query bbox and then builds a vrt

        :param minx: min longitude
        :param miny: min latitude
        :param maxx: max longitude
        :param maxy: max latitude
        :param name: folder name to create for mosaic and the final name of the vrt
        :param em_tol: maximal allowable emission angle, defaults to 10.0
        :param dry_run: set to true to just output how many images would be downloaded
        """
        data = self.get_urls(minx, miny, maxx, maxy, em_tol)
        msg = 'but in dryrun, so will exit...' if dry_run else 'will download now...'
        print(f'Got {len(data)} images to download, {msg}')
        if not dry_run:
            # start downloads
            mkdir('-p', name)
            _download_all(name, data['url'])
            # make vrt
            imgs = [str(x) for x in Path('.').glob(f'./{name}/*.tiff')]
            self._gdalbuildvrt(f'{name}.vrt', '-vrtnodata', '0', '-srcnodata', '0', *imgs, _fg=True)



def main():
    fire.Fire(Circ)
    os._exit(0)

if __name__ == '__main__':
    main()
