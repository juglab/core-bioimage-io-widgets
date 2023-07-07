"""A GUI widget for creating and exporting models compatible with BioImage model zoo."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("core-bioimage-io-widgets")
except PackageNotFoundError:
    __version__ = "uninstalled"

__author__ = "Mehdi Seifi"
__email__ = "mehdiseifi@gmail.com"
