# -*- coding: utf-8 -*-
"""
/***************************************************************************
 imp_ipec
                                 A QGIS plugin
 descarga cartografia desde ipec
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-06-17
        copyright            : (C) 2021 by jlmw78
        email                : j@j.j
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load imp_ipec class from file imp_ipec.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .cartoipec import imp_ipec
    return imp_ipec(iface)