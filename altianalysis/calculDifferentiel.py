import os, sys 
import pathlib
import numpy 
import rasterio
import typing
import numpy as np
import argparse
import logging
from rasterio.enums import Resampling
import requests
import tempfile
import time
from math import ceil


def pretty_time_delta(seconds):
    sign_string = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%s%dd%dh%dm%ds" % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return "%s%dh%dm%ds" % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return "%s%dm%ds" % (sign_string, minutes, seconds)
    else:
        return "%s%ds" % (sign_string, seconds)

def retry(times, delay, factor=2, debug=False):
    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 1
            new_delay = delay
            while attempt <= times:
                need_retry = False
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.ConnectionError as err:
                    print("Connection Error:", err)
                    need_retry = True
                except requests.exceptions.HTTPError as err:
                    if "Server Error" in str(err):
                        print("HTTP Error:", err)
                        need_retry = True
                    else:
                        raise err
                if need_retry:
                    print(f"{attempt}/{times} Nouvel essai après une pause de {pretty_time_delta(new_delay)} .. ")
                    if not debug:
                        time.sleep(new_delay)
                    new_delay = new_delay * factor
                    attempt += 1

            return func(*args, **kwargs)

        return newfn

    return decorator


def is_image_white(filename: str):
    with rasterio.open(filename) as _array:
        raster_array=_array.read()
        band_is_white = [np.all(band == 255) for band in raster_array]
    return np.all(band_is_white)


def download_image_from_geoplateforme(
    proj, layer, minx, miny, maxx, maxy, pixel_per_meter, outfile, timeout, check_images
):
    # Give single-point clouds a width/height of at least one pixel to have valid BBOX and SIZE
    if minx == maxx:
        maxx = minx + 1 / pixel_per_meter
    if miny == maxy:
        maxy = miny + 1 / pixel_per_meter

    # for layer in layers:
    URL_GPP = "https://data.geopf.fr/wms-r/wms?"
    URL_FORMAT = "&EXCEPTIONS=text/xml&FORMAT=image/geotiff&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES="
    URL_EPSG = "&CRS=EPSG:" + str(proj)
    URL_BBOX = "&BBOX=" + str(minx) + "," + str(miny) + "," + str(maxx) + "," + str(maxy)
    URL_SIZE = (
        "&WIDTH="
        + str(ceil((maxx - minx) * pixel_per_meter))
        + "&HEIGHT="
        + str(ceil((maxy - miny) * pixel_per_meter))
    )

    URL = URL_GPP + "LAYERS=" + layer + URL_FORMAT + URL_EPSG + URL_BBOX + URL_SIZE

    print(URL)
    if timeout < 10:
        print(f"Mode debug avec un timeout à {timeout} secondes")

    req = requests.get(URL, allow_redirects=True, timeout=timeout)
    req.raise_for_status()
    print(f"Ecriture du fichier: {outfile}")
    open(outfile, "wb").write(req.content)

    if check_images and is_image_white(outfile):
        raise ValueError(f"Downloaded image is white, with stream: {layer}")


def parse_args():
    parser = argparse.ArgumentParser("compute difference map between lidar dtm and rge alti")
    parser.add_argument("--dtm_lidar_file", type=str, help="dtm lidar tif file")
    #parser.add_argument("--dtm_rge_tile", type=str, help="rge alti tif file")
    parser.add_argument("--name_save_out", type=str, help="name of difference file")
    return parser.parse_args()





def _extract_rge_alti_tile_from_stream(
        dtm_lidar_file: str,
        stream_RGE="RGEALTI-MNT_PYR-ZIP_FXX_LAMB93_WMS",#"ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES",
        proj="2154",
        pixel_per_meter=1,
        timeout_second=300,
        check_images=False
):
    
    # compute dtm lidar extent while reading with rasterio 
    with rasterio.open(dtm_lidar_file) as dtm_lhd:
        bounds=dtm_lhd.bounds
        minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top  
    # apply decorator to retry 3 times, and wait 30 seconds each times
    download_image_from_geoplateforme_retrying = retry(7, 15, 2)(download_image_from_geoplateforme)

    tmp_rge = tempfile.NamedTemporaryFile(suffix="_dtm_rgealti.tif",delete=False)
    download_image_from_geoplateforme_retrying(
        proj, stream_RGE, minx, miny, maxx, maxy, pixel_per_meter, tmp_rge.name, timeout_second, check_images
    )
    return tmp_rge.name


"""
def _compute_difference_with_rge_alti(dtm_lidar_file: str,
                                      dtm_rge_tile: str,
                                      name_save_out: str ) -> None:
    
    # read dtm_lidar tile
    with rasterio.open(dtm_lidar_file) as dtm_lidar, rasterio.open(dtm_rge_tile) as dtm_rge:
        
        # read dtm_lidar array 
        data_dtm_lidar=dtm_lidar.read(1)

        # copy metadata of mtd_lidar 
        meta_dtm_lidar=dtm_lidar.meta.copy()

        # window from rge alti 
        window_rge=dtm_rge.window(*dtm_lidar.bounds)


        # read the data from dtm_rge with the same window as dtm_lidar
        data_dtm_rge_windowed = dtm_rge.read(1, 
                                        window=window_rge, 
                                        boundless=True, 
                                        out_shape=data_dtm_lidar.shape,
                                        resampling=Resampling.cubic,
                                        fill_value=0)
        
        data_dtm_rge_windowed=np.where(data_dtm_rge_windowed==dtm_rge.nodata, 0,data_dtm_rge_windowed)

        # difference dem
        _difference =  data_dtm_lidar - data_dtm_rge_windowed

        # save result 
        with rasterio.open(name_save_out, 'w', **meta_dtm_lidar) as dst:
            dst.write(_difference,1)
"""


def _compute_difference_with_rge_alti(dtm_lidar_file: str,
                                      dtm_rge_tile: str,
                                      name_save_out: str ) -> None:
    
    # read dtm_lidar tile
    with rasterio.open(dtm_lidar_file) as dtm_lidar, rasterio.open(dtm_rge_tile) as dtm_rge:
        
        # read dtm_lidar array 
        data_dtm_lidar=dtm_lidar.read(1)

        # copy metadata of mtd_lidar 
        meta_dtm_lidar=dtm_lidar.meta.copy()

        # window from rge alti 
        window_rge=dtm_rge.window(*dtm_lidar.bounds)


        # read the data from dtm_rge with the same window as dtm_lidar
        data_dtm_rge_windowed = dtm_rge.read(1, 
                                        window=window_rge, 
                                        boundless=True, 
                                        out_shape=data_dtm_lidar.shape,
                                        resampling=Resampling.cubic,
                                        fill_value=0)
        
        #data_dtm_rge_windowed=np.where(data_dtm_rge_windowed==dtm_rge.nodata, 0,data_dtm_rge_windowed)

        # difference dem
        _difference =  data_dtm_lidar - data_dtm_rge_windowed

        _masq_nodata=np.logical_or((data_dtm_rge_windowed==dtm_rge.nodata), (data_dtm_lidar==dtm_lidar.nodata))

        _difference[_masq_nodata]=dtm_lidar.nodata

        # save result 
        with rasterio.open(name_save_out, 'w', **meta_dtm_lidar) as dst:
            dst.write(_difference,1)



def main():   
    args=parse_args()

    tmp_rge=_extract_rge_alti_tile_from_stream(args.dtm_lidar_file,
                                               )

    _compute_difference_with_rge_alti(args.dtm_lidar_file,
                                      tmp_rge,
                                      args.name_save_out)


if __name__=="__main__":
    main()

