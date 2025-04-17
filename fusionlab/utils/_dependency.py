# -*- coding: utf-8 -*-
# Created on Wed Oct 26 17:10:05 2022

from __future__ import annotations

import importlib
import sys
import types
import warnings

from .version import Version

# manage some dependencies when updating versions

VERSIONS = {
    "qtpy":"0.3", 
    "numpydoc": "1.0.4",
    "pyproj":"3.3.0", 
    "tqdm": "4.30.1",
    "pycsamt": "1.1.2" ,
    "xgboost": "1.5.0" ,
    "click":"7.1.2",
    "missingno":"0.5.1" ,
    'pandas_profiling':"0.1.7", 
    "pyjanitor": "0.1",  
    "bs4": "4.8.2",
    "blosc": "1.20.1",
    "bottleneck": "1.3.1",
    "brotli": "0.7.0",
    "fastparquet": "0.4.0",
    "fsspec": "0.7.4",
    "html5lib": "1.1",
    "gcsfs": "0.6.0",
    "jinja2": "2.11",
    "joblib":'1.2.0', 
    "lxml.etree": "4.5.0",
    "markupsafe": "2.0.1",
    "matplotlib": "3.3.2",
    "numba": "0.50.1",
    "numexpr": "2.7.1",
    "odfpy": "1.4.1",
    "openpyxl": "3.0.3",
    "pandas_gbq": "0.14.0",
    "psycopg2": "2.8.4",  # (dt dec pq3 ext lo64)
    "pymysql": "0.10.1",
    "pyarrow": "1.0.1",
    "pyreadstat": "1.1.0",
    "pytest": "6.0",
    "pyxlsb": "1.0.6",
    "s3fs": "0.4.0",
    "scipy": "1.4.1",
    "snappy": "0.6.0",
    "sqlalchemy": "1.4.0",
    "tables": "3.6.1",
    "tabulate": "0.8.7",
    "xarray": "0.15.1",
    "xlrd": "2.0.1",
    "xlwt": "1.3.0",
    "xlsxwriter": "1.2.2",
    "yellowbrick": "1.5.0", 
    "zstandard": "0.15.2",
}

# A mapping from import name to package name (on PyPI) for packages where
# these two names are different.

INSTALL_MAPPING = {
    "bs4": "beautifulsoup4",
    "bottleneck": "Bottleneck",
    "brotli": "brotlipy",
    "jinja2": "Jinja2",
    "lxml.etree": "lxml",
    "odf": "odfpy",
    "pandas_gbq": "pandas-gbq",
    "snappy": "python-snappy",
    "sqlalchemy": "SQLAlchemy",
    "tables": "pytables",
}


def get_version(module: types.ModuleType) -> str:
    version = getattr(module, "__version__", None)
    if version is None:
        # xlrd uses a capitalized attribute name
        version = getattr(module, "__VERSION__", None)

    if version is None:
        if module.__name__ == "brotli":
            # brotli doesn't contain attributes to confirm it's version
            return ""
        if module.__name__ == "snappy":
            # snappy doesn't contain attributes to confirm it's version
            # See https://github.com/andrix/python-snappy/pull/119
            return ""
        raise ImportError(f"Can't determine version for {module.__name__}")
    if module.__name__ == "psycopg2":
        # psycopg2 appends " (dt dec pq3 ext lo64)" to it's version
        version = version.split()[0]
    return version

def import_optional_dependency(
    name: str,
    extra: str = "",
    errors: str = "raise",
    min_version: str | None = None,
    exception:Exception=None 
):
    """
    Import an optional dependency.

    By default, if a dependency is missing an ImportError with a nice
    message will be raised. If a dependency is present, but too old,
    we raise.

    Parameters
    ----------
    name : str
        The module name.
    extra : str
        Additional text to include in the ImportError message.
    errors : str {'raise', 'warn', 'ignore'}
        What to do when a dependency is not found or its version is too old.

        * raise : Raise an ImportError
        * warn : Only applicable when a module's version is to old.
          Warns that the version is too old and returns None
        * ignore: If the module is not installed, return None, otherwise,
          return the module, even if the version is too old.
          It's expected that users validate the version locally when
          using ``errors="ignore"`` (see. ``io/html.py``)
    min_version : str, default None
        Specify a minimum version that is different from the global pandas
        minimum version required.
    exception: callable, BaseException
        Can be your own package exception rather than ImportError 
    Returns
    -------
    maybe_module : Optional[ModuleType]
        The imported module, when found and the version is correct.
        None is returned when the package is not found and `errors`
        is False, or when the package's version is too old and `errors`
        is ``'warn'``.
    """

    assert errors in {"warn", "raise", "ignore"}

    package_name = INSTALL_MAPPING.get(name)
    install_name = package_name if package_name is not None else name
    
    exception = ImportError  if exception is None else exception 
    if not callable (exception):
        exception = ImportError 
    
    msg = (
        f"Missing optional dependency '{install_name}'. {extra} "
        f"Use pip or conda to install {install_name}."
    )
    try:
        module = importlib.import_module(name)
    except ImportError:
        if errors == "raise":
            raise exception (msg )
        else:
            return None

    # Handle submodules: if we have submodule, grab parent module from sys.modules
    parent = name.split(".")[0]
    if parent != name:
        install_name = parent
        module_to_get = sys.modules[install_name]
    else:
        module_to_get = module
    minimum_version = min_version if min_version is not None else VERSIONS.get(parent)
    if minimum_version:
        version = get_version(module_to_get)
        if version and Version(version) < Version(minimum_version):
            msg = (
                f"Watex requires version '{minimum_version}' or newer of '{parent}' "
                f"(version '{version}' currently installed)."
            )
            if errors == "warn":
                warnings.warn(msg, UserWarning)
                return None
            elif errors == "raise":
                raise exception(msg)

    return module