import fire
import moody.moody as moody
import os
from pathlib import Path
import geopandas as gpd
from sh import Command
from deco import *
import shapely.geometry
import tqdm

@concurrent
def _download(path, url, i, h):
    from sh import wget
    name = url.split('/')[-1]
    # perform download in fg so that progress is reported.
    wget('-O', f'{path}/{name}', url, '--continue', '-q', '--show-progress', _fg=True)
    print(f'\nCompleted {name}, {i+1}/{h}')

@synchronized
def _download_all(path, urls):
    how_many = len(urls)
    for i, url in enumerate(urls):
        _download(path, url, i, how_many)


class Circ(object):

    def __init__(self, https: bool = False):
        self._here = Path(os.path.realpath(__file__)).parent
        self._https = https
        self._ctx_shp = str(self._here / 'data' / 'mars_mro_ctx_edr_m_c0a' / 'mars_mro_ctx_edr_m_c0a.shp')
        self._ode = moody.ODE(https=self._https)

    @staticmethod
    def _reduce(data: gpd.GeoDataFrame, shuffle: bool = False, fraction: float = .99)-> gpd.GeoDataFrame:
        """
        Perform reduction of ctx footprint overlaps, with tunable
        random shuffles and fractional overlap
        :param data: GeoDataFrame of footprints
        :param shuffle: Flag to turn on shuffle reduce mode
        :param fraction: Overlap allowable (default 99% overlap or less is ok)
        :return: GeoDataFrame of results
        """
        tot_shape = None
        collection = []
        data_iter = data.sample(frac=1) if shuffle else data
        for c in tqdm.tqdm(data_iter.itertuples(), total=len(data), leave=False):
            if tot_shape is None:
                tot_shape = shapely.geometry.Polygon(c.geometry)
                collection.append(c)
            else:
                intersection = tot_shape.intersection(c.geometry)
                if intersection.area / c.geometry.area <= fraction:
                    tot_shape = tot_shape.union(c.geometry)
                    collection.append(c)

        return gpd.GeoDataFrame(collection)

    def get_asu_url(self, pid: str)-> str:
        """
        Ge the url for the ASU produced CTX geotiff from the pid
        :param pid: ctx product id
        :return: url string
        """
        index = self._ode.get_ctx_meta_by_key(pid, 'LabelURL')
        mrox = index.split('/')[-3]
        url = f'http://image.mars.asu.edu/stream/{pid}.tiff?image=/mars/images/ctx/{mrox}/prj_full/{pid}.tiff'
        return url

    def select_imgs(self, minx: float, miny: float, maxx: float, maxy: float, em_tol: float = 5.0, num_iters: int = 25)-> gpd.GeoDataFrame:
        """
        Perform the image selection query given the bbox and other params
        then reduce the collection to minimize redundant images

        :param minx: min longitude
        :param miny: min latitude
        :param maxx: max longitude
        :param maxy:  max latitude
        :param em_tol: maximal allowable emission angle, defaults to 5.0
        :param num_iters: number of times to perform the shuffle reduction step,
         25 appears to be more than enough with areas I tried.
        :return: geodataframe
        """
        query_res = gpd.GeoDataFrame(gpd.read_file(self._ctx_shp).cx[minx:maxx, miny:maxy])
        query_res['area'] = query_res.area
        query_res = self._reduce(query_res[query_res['EmAngle'] <= em_tol].sort_values(['EmAngle', 'area'], ascending=[True, False]))
        query_res = self._reduce(query_res.sort_values('area', ascending=False))
        # simplistic way to reduce number of images,
        # yes, I know using a tree would be better but whatevs
        for _ in tqdm.trange(num_iters, leave=True, desc="shuffle reduce"):
            query_res = self._reduce(query_res, shuffle=True)

        return query_res

    def get_urls(self, minx: float, miny: float, maxx: float, maxy: float, em_tol: float = 5.0)-> gpd.GeoDataFrame:
        """
        Perform the spatial query and overlap reduction to return a dataframe
        with the results including a field for the url

        :param minx: min longitude
        :param miny: min latitude
        :param maxx: max longitude
        :param maxy:  max latitude
        :param em_tol: maximal allowable emission angle, defaults to 5.0
        :return: geodataframe including url field
        """
        res = self.select_imgs(minx, miny, maxx, maxy, em_tol)
        res['url'] = [self.get_asu_url(pid) for pid in res['ProductId']]
        return res

    def make_vrt(self, minx: float, miny: float, maxx: float, maxy: float, name: str = 'mosaic', em_tol: float = 5.0, dry_run: bool = False) -> None:
        """
        Search for, then downloads all ctx images within query bbox and then builds a vrt

        :param minx: min longitude
        :param miny: min latitude
        :param maxx: max longitude
        :param maxy: max latitude
        :param name: folder name to create for mosaic and the final name of the vrt
        :param em_tol: maximal allowable emission angle, defaults to 5.0
        :param dry_run: set to true to just output how many images would be downloaded
        """
        print("Looking for images in that area 🌐...")
        data = self.get_urls(minx, miny, maxx, maxy, em_tol)
        msg = 'In dry run, so no more work to do! 🍻' if dry_run else 'will download now...'
        print(f'Got {len(data)} images to download, {msg}')
        if not dry_run:
            # start downloads
            Path(f'./{name}').mkdir(exist_ok=True)
            _download_all(name, data['url'])
            # make vrt
            imgs = [str(x) for x in Path('.').glob(f'./{name}/*.tiff')]
            print(f'Running gdalbuildvrt on ./{name}/*.tiff')
            gdalbuildvrt = Command('gdalbuildvrt')
            gdalbuildvrt(f'{name}.vrt', '-vrtnodata', '0', '-srcnodata', '0', *imgs, _fg=True)
            print(f'Done! 🎉🎉🎉   See vrt image: ./{name}.vrt')


def main():
    fire.Fire(Circ)
    # exit faster
    os._exit(0)

if __name__ == '__main__':
    main()
