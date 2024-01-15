import pytest
from qgis.core import (QgsPointXY, QgsGeometry, QgsFeature)

from . import gdf, GeoDataFarm

# @pytest.mark.depends(scope='session', name='add_field')
def test_add_field(gdf: GeoDataFarm):
    gdf.add_field.clicked_define_field()
    gdf.add_field.AFD.LEFieldName.setText('test_field')
    feat = QgsFeature(gdf.add_field.field.fields()) # Create the features
    pointxys = []
    coords = [[55.39658060, 13.55289676], [55.39478077, 13.55261314], [55.39429053, 13.55921056], [55.39625846, 13.55940787]]
    for coord in coords:
        pointxys.append(QgsPointXY(coord[1], coord[0])) 
    geom = QgsGeometry.fromPolygonXY([pointxys])
    feat.setGeometry(geom)
    gdf.add_field.field.addFeature(feat)
    gdf.add_field.field.endEditCommand() # Stop editing
    gdf.add_field.field.commitChanges() # Save changes
    gdf.add_field.save()

# @pytest.mark.depends(scope='session', name='add_field2')
def test_add_sec_field(gdf: GeoDataFarm):
    gdf.add_field.clicked_define_field()
    gdf.add_field.AFD.LEFieldName.setText('test_iso_field')
    feat = QgsFeature(gdf.add_field.field.fields()) # Create the features
    pointxys = []
    coords = [[55.39185207, 13.53883729], [55.39802257, 13.53983692], [55.39745005, 13.54726151], [55.39066160, 13.54608921]]
    for coord in coords:
        pointxys.append(QgsPointXY(coord[1], coord[0])) 
    geom = QgsGeometry.fromPolygonXY([pointxys])
    feat.setGeometry(geom)
    gdf.add_field.field.addFeature(feat)
    gdf.add_field.field.endEditCommand() # Stop editing
    gdf.add_field.field.commitChanges() # Save changes
    gdf.add_field.save()

