"""Have a widget that consumers (e.g. in napari) can use to make their BioImage.io zip export"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("core-bioimage-io-widgets")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Mehdi Seifi"
__email__ = "mehdiseifi@gmail.com"
