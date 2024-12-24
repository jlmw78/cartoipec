import os
import csv
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .resources import *
from .cartoipec_v2_dialog import cartoipecv2Dialog
from osgeo import ogr
from qgis.core import QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem

class cartoipecv2:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Cargar traducciones
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'cartoipecv2_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Inicializar listado como un atributo de la clase
        self.listado = self.load_localidades()

        self.actions = []
        self.menu = self.tr(u'&CartoIpec_v2')
        self.first_start = True

    def load_localidades(self):
        """Carga las localidades desde un archivo CSV."""
        listado = {}
        csv_file_path = os.path.join(self.plugin_dir, 'localidades.csv')

        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                nom_dep = row['NomDep']
                nom_loc = row['NomLoc']
                zip2010 = row['zip2010']
                zip2022 = row['zip2022']

                if nom_dep not in listado:
                    listado[nom_dep] = {}
                listado[nom_dep][nom_loc] = (zip2010, zip2022)

        return listado

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('cartoipecv2', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        
        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/cartoipec_v2/logo.png'
        self.add_action(icon_path, text=self.tr(u'Carto_Ipec_v2'), callback=self.run,
                        parent=self.iface.mainWindow())
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&CartoIpec_v2'), action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""
        self.dlg = cartoipecv2Dialog()

        # Conectar la señal del comboBox al método que actualiza comboBox_2
        self.dlg.comboBox.currentIndexChanged.connect(self.update_comboBox_2)

        # Añadir localidades al comboBox y agregar la opción 'todo'
        departamentos = list(self.listado.keys())
        departamentos.insert(0, 'todo')  # Agregar 'todo' al inicio de la lista
        self.dlg.comboBox.addItems(departamentos)

        # Mostrar el diálogo
        result = self.dlg.exec_()

        # Verificar si se presionó OK
        if result:
            departamento = self.dlg.comboBox.currentText()  # Obtener el departamento seleccionado
            localidad_seleccionado = self.dlg.comboBox_2.currentText()  # Obtener la localidad seleccionada

            # Manejar el caso donde se selecciona 'todo'
            if departamento == 'todo':
                if localidad_seleccionado:
                    zip_files = []
                    for dep in self.listado.keys():
                        if localidad_seleccionado in self.listado[dep]:
                            zip_files.append(self.listado[dep][localidad_seleccionado])
                    if not zip_files:
                        print(f"No se encontró el nombreZip '{localidad_seleccionado}' en ninguna localidad.")
                        return

                    # Dependiendo del valor de los radioButton
                    if self.dlg.radioButton.isChecked():
                        layer_name = zip_files[0][0]  # Primer elemento de la tupla (zip2010)
                        zipbase = '/vsizip//vsicurl/https://www.santafe.gov.ar/ipecinformes/uploads/planta_2010/' + layer_name + '.zip'
                        version = ' - 2010'
                    elif self.dlg.radioButton_2.isChecked():
                        layer_name = zip_files[0][1]  # Segundo elemento de la tupla (zip2022)
                        zipbase = '/vsizip//vsicurl/https://www.santafe.gov.ar/ipecinformes/uploads/planta/' + layer_name + '.zip'
                        version = ' - 2022'

            else:
                # Solo proceder si hay una localidad seleccionada
                if localidad_seleccionado and departamento in self.listado:
                    if localidad_seleccionado in self.listado[departamento]:
                        if self.dlg.radioButton.isChecked():
                            layer_name = self.listado[departamento][localidad_seleccionado][0]  # Primer elemento de la tupla (zip2010)
                            zipbase = '/vsizip//vsicurl/https://www.santafe.gov.ar/ipecinformes/uploads/planta_2010/' + layer_name + '.zip'
                            version = ' - 2010'
                        elif self.dlg.radioButton_2.isChecked():
                            layer_name = self.listado[departamento][localidad_seleccionado][1]  # Segundo elemento de la tupla (zip2022)
                            zipbase = '/vsizip//vsicurl/https://www.santafe.gov.ar/ipecinformes/uploads/planta/' + layer_name + '.zip'
                            version = ' - 2022'
                    else:
                        print(f"No se encontró la localidad '{localidad_seleccionado}' en el departamento '{departamento}'.")
                        return

            # Crear el grupo con el nombre de localidad seleccionado
            root = QgsProject.instance().layerTreeRoot()
            grupo = root.addGroup(localidad_seleccionado + version)
            shapefiles = [layer.GetName() for layer in ogr.Open(zipbase)]
            layers = []

            # Lee los shapefiles contenidos en el zip
            for shp_name in shapefiles:
                shp_path = f"{zipbase}/{shp_name}.shp"
                vl = QgsVectorLayer(shp_path, shp_name, 'ogr')  # Crea la capa vectorial
                vl.setCrs(QgsCoordinateReferenceSystem('EPSG:22185'))  # Designa el sistema de proyección...
                layers.append(vl)
                grupo.addLayer(vl)  # Agrega la capa al grupo

            # Carga las capas sin mostrarlas
            QgsProject.instance().addMapLayers(layers, False)

            # Asigno estilos y carga las capas
            vl_names = []
            for layer in QgsProject.instance().mapLayers().values():
                vl_names.append(layer.name())
                
                if layer.name().startswith('E'):
                    style_path = self.plugin_dir + '/estilos/style_E.qml'
                    layer.loadNamedStyle(style_path)
                elif layer.name().startswith('e'):
                    style_path = self.plugin_dir + '/estilos/style_E_2022.qml'
                    layer.loadNamedStyle(style_path)
                elif layer.name().startswith('M'):
                    style_path = self.plugin_dir + '/estilos/style_M.qml'
                    layer.loadNamedStyle(style_path)
                elif layer.name().startswith('m'):
                    style_path = self.plugin_dir + '/estilos/style_M.qml'
                    layer.loadNamedStyle(style_path)
                elif layer.name().startswith('R'):
                    style_path = self.plugin_dir + '/estilos/style_R.qml'
                    layer.loadNamedStyle(style_path)
                elif layer.name().startswith('r'):
                    style_path = self.plugin_dir + '/estilos/style_R.qml'
                    layer.loadNamedStyle(style_path)

                try:
                    print(f"Estilo aplicado a {layer.name()}: {style_path}")
                except Exception as e:
                    print(f"Error al cargar el estilo para {layer.name()}: {e}")


    def update_comboBox_2(self):
        """Actualiza comboBox_2 con elementos que coinciden con el valor seleccionado en comboBox."""
        selected_departamento = self.dlg.comboBox.currentText()  # Obtener el valor seleccionado en comboBox
        
        # Limpiar comboBox_2 antes de agregar nuevos elementos
        self.dlg.comboBox_2.clear()
        
        # Obtener los elementos correspondientes al valor seleccionado
        if selected_departamento == 'todo':
            # Si se selecciona 'todo', agregar todos localidades
            for localidades in self.listado.values():
                for localidades in localidades.keys():
                    self.dlg.comboBox_2.addItem(localidades)
                    
        elif selected_departamento in self.listado:
            for localidades in self.listado[selected_departamento].keys():
                self.dlg.comboBox_2.addItem(localidades)
