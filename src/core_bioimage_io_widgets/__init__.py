"""A BioImage.io widget to export model zip file using ui provided by this widget."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("core-bioimage-io-widgets")
except PackageNotFoundError:
    __version__ = "uninstalled"

__author__ = "Mehdi Seifi"
__email__ = "mehdiseifi@gmail.com"
