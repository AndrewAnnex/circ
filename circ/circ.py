import fire
import moody.moody as moody
import os
from pathlib import Path
import shapely
from shapely.geometry import shape
import geopandas as gpd
from sh import mkdir, cd, cwd, Command
from deco import concurrent

here = Path(os.path.realpath(__file__))

class Circ(object):

    def __init__(self, https=False):
        self.ode = moody.ODE(https=https)
        self.ctx_shp = here / 'data' / 'mars_mro_ctx_edr_m_c0a' / 'mars_mro_ctx_edr_m_c0a.shp'
        self.ctx =  gpd.read_file(self.ctx_shp)
        self.gdalbuildvrt = Command('gdalbuildvrt')

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
        index = self.ode.get_ctx_meta_by_key(pid, 'LabelURL')
        mrox = index.split('/')[-3]
        url = f'http://image.mars.asu.edu/stream/{pid}.tiff?image=/mars/images/ctx/{mrox}/prj_full/{pid}.tiff'
        return url

    def select_imgs(self, minx, miny, maxx, maxy, em_tol=10.0)-> gpd.GeoDataFrame:
        query_res = gpd.GeoDataFrame(self.ctx.cx[minx:maxx, miny:maxy])
        query_res['area'] = query_res.area
        query_res = self._reduce(query_res[query_res['EmAngle'] <= em_tol].sort_values(['EmAngle', 'area'], ascending=[True, False]))
        query_res = self._reduce(query_res.sort_values('area', ascending=False))
        # simplistic way to reduce number of images,
        # yes, I know using a tree would be better but whatevs
        for i in range(25):
            query_res = self._shuffle_reduce(query_res)

        return query_res

    def get_urls(self, minx, miny, maxx, maxy, em_tol=10.0)-> gpd.GeoDataFrame:
        res = self.select_imgs(minx, miny, maxx, maxy, em_tol)
        res['url'] = [self.get_asu_url(pid) for pid in res['ProductId']]
        return res

    @staticmethod
    def download_urls(data: gpd.GeoDataFrame):
        @concurrent
        def _download(url):
            name = url.split('/')[-1]
            moody.download_file(url, name, 1024*1000)
        for url in data['url']:
            _download(url)

    def make_vrt(self, minx, miny, maxx, maxy, name='mosaic', em_tol=10.0):
        data = self.get_urls(minx, miny, maxx, maxy, em_tol)
        # start downloads
        top = cwd()
        mkdir('-p', name)
        cd(name)
        self.download_urls(data)
        cd(top)
        # make vrt
        self.gdalbuildvrt(f'{name}.vrt', f'{name}/*.tiff', _fg=True)




def main():
    fire.Fire(Circ)

if __name__ == '__main__':
    main()
