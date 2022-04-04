import numpy as np
from operator import xor
import pandas as pd
from PyQt5 import QtWidgets, QtCore

from ..import_data.handle_text_data import create_table, create_polygons
from ..support_scripts.__init__ import (TR, check_text)
from ..support_scripts.radio_box import RadioComboBox
from ..support_scripts.pyagriculture.agriculture import PyAgriculture
from ..widgets.import_xml_bin import ImportXmlBin


class Iso11783:
    def __init__(self, parent_widget, type_: str):
        """For supporting the read of iso XML/Bin files"""
        self.py_agri = None
        self.db = parent_widget.db
        self.populate = parent_widget.populate
        self.data_type = type_
        self.sender = QtWidgets.QWidget().sender
        self.IXB = ImportXmlBin()
        self.py_agri = None
        translate = TR('ImportXmlBin')
        self.tr = translate.tr
        self.combo = []
        self.tasks = []
        self.checkboxes1 = []
        self.checkboxes2 = []
        self.checkboxes3 = []
        self.checkboxes4 = []
        self.unit_boxes = {}

    def initiate_pyAgriculture(self, path: str):
        """Connects the plugin to pyAgriculture."""
        self.py_agri = PyAgriculture(path)
        self.py_agri.read_with_cython = False

    def run(self):
        """Presents the sub widget ImportXmlBin and connects the different
        buttons to their function."""
        self.IXB.show()
        self.IXB.PBAddInputFolder.clicked.connect(self.open_input_folder)
        self.IXB.PBFindFields.clicked.connect(self.populate_second_table)
        self.IXB.PBAddParam.clicked.connect(self.add_to_param_list)
        self.IXB.PBRemParam.clicked.connect(self.remove_from_param_list)
        self.IXB.PBInsert.clicked.connect(self.add_to_database)
        self.IXB.exec_()

    def close(self):
        """Disconnects buttons and closes the widget"""
        self.IXB.PBAddInputFolder.clicked.disconnect()
        self.IXB.PBFindFields.clicked.disconnect()
        self.IXB.PBAddParam.clicked.disconnect()
        self.IXB.PBRemParam.clicked.disconnect()
        self.IXB.PBInsert.clicked.disconnect()
        self.IXB.done(0)

    def open_input_folder(self):
        """Opens a dialog and let the user select the folder where Taskdata are stored."""
        path = QtWidgets.QFileDialog.getExistingDirectory(None, self.tr("Open a folder"), '',
                                                          QtWidgets.QFileDialog.ShowDirsOnly)
        if path != '':
            self.initiate_pyAgriculture(path)
            self.populate_first_table()

    def get_task_data(self) -> dict:
        """For those tasks that are marked with include the script will gather their data."""
        task_names = {}
        for task_nr, data_set in enumerate(self.py_agri.tasks):  # type: pd.DataFrame
            try:
                mid_rw = int(len(data_set) / 2)
                lat = data_set.iloc[mid_rw]['latitude']
                lon = data_set.iloc[mid_rw]['longitude']
                time_stamp = data_set.iloc[mid_rw]['time_stamp']
                if lat is None or lon is None or time_stamp is None:
                    continue
            except Exception as e:
                print(f'error: {e}')
                return
            fields = []
            fields_ = self.db.execute_and_return(f"""select field_name from fields where st_intersects(polygon, st_geomfromtext('Point({lon} {lat})', 4326))""")
            for field in fields_:
                fields.append([field, time_stamp])
            task_names[task_nr] = fields
        return task_names

    def populate_first_table(self):
        """Populates the task list."""
        self.checkboxes1 = []
        task_names = self.py_agri.gather_task_names()
        self.IXB.TWISODataAll.setRowCount(len(task_names))
        self.IXB.TWISODataAll.setColumnCount(2)
        self.IXB.TWISODataAll.setHorizontalHeaderLabels([self.tr('Get more info'), self.tr('Task name')])
        self.IXB.TWISODataAll.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        for i, row in enumerate(task_names):
            item1 = QtWidgets.QTableWidgetItem('Include')
            item1.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item1.setCheckState(QtCore.Qt.Checked)
            self.checkboxes1.append([item1, row])
            item2 = QtWidgets.QTableWidgetItem(row)
            item2.setFlags(xor(item2.flags(), QtCore.Qt.ItemIsEditable))
            self.IXB.TWISODataAll.setItem(i, 0, item1)
            self.IXB.TWISODataAll.setItem(i, 1, item2)

    def populate_second_table(self):
        """Populates the list that is marked as include in the first table."""
        tasks_to_include = []
        for row in self.checkboxes1:
            if row[0].checkState() == 2:
                tasks_to_include.append(row[1])
        if len(tasks_to_include) is 0:
            QtWidgets.QMessageBox.information(None, self.tr("Error:"),
                                              self.tr('You need to select at least one of the tasks'))
            return
        self.py_agri.tasks = []
        self.combo = []
        self.checkboxes2 = []
        self.checkboxes3 = []
        self.checkboxes4 = []
        self.py_agri.gather_data(only_tasks=tasks_to_include)
        task_names = self.get_task_data()
        self.IXB.TWISODataSelect.setRowCount(len(tasks_to_include))
        self.IXB.TWISODataSelect.setColumnCount(4)
        self.IXB.TWISODataSelect.setHorizontalHeaderLabels([self.tr('To include'), self.tr('Date'), self.tr('Field'),
                                                            self.tr('Crops')])
        self.IXB.TWISODataSelect.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        j = -1  # How may checkboxes that is added
        for i, row in enumerate(task_names.items()):
            if len(row[1]) == 0:
                continue
            j += 1
            item1 = QtWidgets.QTableWidgetItem('Include')
            item1.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item1.setCheckState(QtCore.Qt.Checked)
            self.checkboxes2.append([i, j, item1])
            item2 = QtWidgets.QTableWidgetItem(row[1][0][1])
            item2.setFlags(xor(item2.flags(), QtCore.Qt.ItemIsEditable))
            field_column = RadioComboBox()
            self.combo.append(field_column)
            self.populate.reload_fields(field_column)
            for nr in range(field_column.count()):
                if field_column.itemText(nr) == row[1][0][0][0]:
                    item = field_column.model().item(nr, 0)
                    item.setCheckState(QtCore.Qt.Checked)
                    field_column.setCurrentIndex(nr)
            crops = QtWidgets.QComboBox()
            self.populate.reload_crops(crops)
            self.IXB.TWISODataSelect.setItem(i, 0, item1)
            self.IXB.TWISODataSelect.setItem(i, 1, item2)
            self.IXB.TWISODataSelect.setCellWidget(i, 2, field_column)
            self.IXB.TWISODataSelect.setCellWidget(i, 3, crops)
            self.checkboxes3.append(field_column)
            self.checkboxes4.append(crops)
            self.tasks.append(self.py_agri.tasks[i])
        self.set_column_list()

    def add_to_param_list(self):
        """Adds the selected columns to the list of fields that should be
        treated as "special" in the database both to work as a parameter that
        could be evaluated and as a layer that is added to the canvas"""
        rows_in_table = self.IXB.TWtoParam.rowCount()
        self.IXB.TWtoParam.setColumnCount(1)
        items_to_add = []
        existing_values = []
        for i in range(rows_in_table):
            existing_values.append(self.IXB.TWtoParam.item(i, 0).text())
        for i, item in enumerate(self.IXB.TWColumnNames.selectedItems()):
            if item.column() == 0 and item.text() not in existing_values:
                index = self.IXB.TWColumnNames.selectedIndexes()[i].row()
                items_to_add.append(item.text() +
                                    f'_{check_text(self.IXB.TWColumnNames.cellWidget(index, 4).currentText())}_')
        for i, item in enumerate(items_to_add):
            self.IXB.TWtoParam.setRowCount(rows_in_table + i + 1)
            item1 = QtWidgets.QTableWidgetItem(item)
            item1.setFlags(xor(item1.flags(), QtCore.Qt.ItemIsEditable))
            self.IXB.TWtoParam.setItem(i, 0, item1)
        self.IXB.PBInsert.setEnabled(True)

    def remove_from_param_list(self):
        """Removes the selected columns from the list of fields that should be
        treated as "special" in the database"""
        if self.IXB.TWtoParam.selectedItems() is None:
            QtWidgets.QMessageBox.information(None, self.tr("Error:"), self.tr('No row selected!'))
            return
        for item in self.IXB.TWtoParam.selectedItems():
            self.IXB.TWtoParam.removeRow(item.row())
        if self.IXB.TWtoParam.rowCount() == 0:
            self.IXB.PBInsert.setEnabled(False)

    def set_column_list(self):
        """A function that retrieves the name of the columns from the first tasks"""
        self.IXB.TWColumnNames.clear()
        self.combo = []
        self.IXB.TWColumnNames.setRowCount(len(self.tasks[0].columns))
        self.IXB.TWColumnNames.setColumnCount(6)
        self.IXB.TWColumnNames.setHorizontalHeaderLabels([self.tr('Column name'), self.tr('Mean value'), self.tr('Min value'), self.tr('Max value'), self.tr('Unit'), self.tr('Scale')])
        self.unit_boxes = {}
        self.IXB.TWColumnNames.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        for i, row in enumerate(self.tasks[0].columns):
            item1 = QtWidgets.QTableWidgetItem(row)
            item1.setFlags(xor(item1.flags(), QtCore.Qt.ItemIsEditable))
            self.IXB.TWColumnNames.setItem(i, 0, item1)
            try:
                mean = str(round(self.tasks[0][row].mean(), 2))
            except:
                mean = ''
            item2 = QtWidgets.QTableWidgetItem(mean)
            self.IXB.TWColumnNames.setItem(i, 1, item2)
            try:
                _min = str(self.tasks[0][row].min())
            except:
                _min = ''
            item3 = QtWidgets.QTableWidgetItem(_min)
            self.IXB.TWColumnNames.setItem(i, 2, item3)
            try:
                _max = str(self.tasks[0][row].max())
            except:
                _max = ''
            item4 = QtWidgets.QTableWidgetItem(_max)
            self.IXB.TWColumnNames.setItem(i, 3, item4)
            unit = self.tasks[0].attrs['unit_row'][i]
            unit_col = self.get_units_option(unit)
            self.unit_boxes[len(self.unit_boxes)] = {'box': unit_col, 'org_item': unit}
            unit_col.__setattr__('index', i)
            unit_col.__setattr__('org_item', unit)
            unit_col.currentTextChanged.connect(self.change_unit_type)
            self.IXB.TWColumnNames.setCellWidget(i, 4, unit_col)
            item6 = QtWidgets.QTableWidgetItem("1")
            self.IXB.TWColumnNames.setItem(i, 5, item6)

    def change_unit_type(self):
        index = self.sender().index
        org_item = self.sender().org_item
        new_unit = self.IXB.TWColumnNames.cellWidget(index, 4).currentText()
        if org_item == new_unit:
            return
        new_value = None
        if org_item == 'ft':
            if new_unit == 'in':
                new_value = 12
            if new_unit == 'cm':
                new_value = 30.48
            if new_unit == 'm':
                new_value = 0.3048
        if org_item == 'in':
            if new_unit == 'in':
                new_value = 1 / 12
            if new_unit == 'cm':
                new_value = 2.54
            if new_unit == 'm':
                new_value = 0.0254
        if org_item == 'lb/bu':
            if new_unit == 'kg/m3':
                new_value = 12.87
        if org_item == 'lb/h':
            if new_unit =='kg/h':
                new_value = 0.453592
        if org_item == 'ac/h':
            if new_unit == 'ha/h':
                new_value = 0.404686
        if new_unit == 'kg/ha':
            if org_item == 'bu/ac':
                new_value = 67
            if org_item == 'lb/ac':
                new_value = 1.12085
        if org_item == 'gal/h':
            if new_unit == 'l/h':
                new_value = 3.7854
        if new_unit == 'C':
            new_value = 'C'
        if new_unit == 'F':
            new_value = 'F'
        if new_value is not None:
            self.IXB.TWColumnNames.item(index, 5).setText(str(new_value))

    @staticmethod
    def get_units_option(org_unit) -> RadioComboBox:
        unit_col = RadioComboBox()
        unit_col.addItem(org_unit)
        if org_unit == 'C':
            unit_col.addItem('F')
        if org_unit == 'F':
            unit_col.addItem('C')
        if org_unit == 'ft':
            unit_col.addItem('in')
            unit_col.addItem('cm')
            unit_col.addItem('m')
        if org_unit == 'in':
            unit_col.addItem('ft')
            unit_col.addItem('cm')
            unit_col.addItem('m')
        if org_unit == 'lb/bu':
            unit_col.addItem('kg/m3')
        if org_unit == 'lb/h':
            unit_col.addItem('kg/h')
        if org_unit == 'ac/h':
            unit_col.addItem('ha/h')
        if org_unit in ['bu/ac', 'lb/ac']:
            unit_col.addItem('kg/ha')
        if org_unit == 'gal/h':
            unit_col.addItem('l/h')
        return unit_col

    @staticmethod
    def cel2far(celsius) -> float:
        fahrenheit = 9.0 / 5.0 * celsius + 32
        return fahrenheit

    @staticmethod
    def far2cel(fahrenheit) -> float:
        celsius = (fahrenheit - 32) * 5.0 / 9.0
        return  celsius

    def prep_data(self) -> list:
        """Gather data from the combo-checkboxes and check that they are valid."""
        fields = []
        crops = []
        dates = []
        focus_cols = []
        focus_col = []
        idxs = []
        rows_in_table = self.IXB.TWtoParam.rowCount()
        for i in range(rows_in_table):
            focus_col.append(check_text(self.IXB.TWtoParam.item(i, 0).text()))
        found = False
        for tbl_idx, check_idx,  cbox in self.checkboxes2:
            if cbox.checkState() == 2:
                found = True
                dates.append(self.IXB.TWISODataSelect.item(tbl_idx, 1).text())
                field = self.checkboxes3[check_idx].currentText()
                if field == self.tr('--- Select field ---'):
                    QtWidgets.QMessageBox.information(None, self.tr("Error:"),
                                                      self.tr('You need to select a crop'))
                    return [False]
                fields.append(field)
                crop = self.checkboxes4[check_idx].currentText()
                if crop == self.tr('--- Select crop ---'):
                    QtWidgets.QMessageBox.information(None, self.tr("Error:"),
                                                      self.tr('You need to select a crop'))
                    return [False]
                crops.append(crop)
                focus_cols.append(focus_col)
                idxs.append(tbl_idx)
        if not found:
            QtWidgets.QMessageBox.information(None, self.tr("Error:"),
                                              self.tr('You need to select at least one of the tasks'))
            return [False]
        return [True, fields, crops, dates, focus_cols, idxs]

    def scale_dfs(self, df) -> list:
        for col_id, col in enumerate(df.columns):
            scale_f = self.IXB.TWColumnNames.item(col_id, 5).text()
            if scale_f == 'C':
                df[col] = self.far2cel(df[col])
                continue
            elif scale_f == 'F':
                df[col] = self.cel2far(df[col])
                continue
            try:
                value = float(scale_f)
                df[col] = df[col] * value
            except ValueError:
                QtWidgets.QMessageBox(None, self.tr('Error'), self.tr('The number must only contain numbers and .'))
                return [False]
            except TypeError:
                pass
        return [True, df]

    def get_col_types(self) -> list:
        """Gather the column types (0=int, 1=float, 2=string)"""
        col_types = []
        for dtype in self.py_agri.tasks[0].dtypes:
            if dtype == np.int64:
                col_types.append(0)
            elif dtype == np.float64:
                col_types.append(1)
            elif dtype == np.str_:
                col_types.append(2)
            else:
                col_types.append(2)
        return col_types

    def get_col_units(self) -> list:
        """returns a list with the unit of all columns, if None '' is added."""
        col_units = []
        for index in range(self.IXB.TWColumnNames.rowCount()):
            new_unit = self.IXB.TWColumnNames.cellWidget(index, 4).currentText()
            if new_unit != '':
                col_units.append(f'_{check_text(new_unit)}_')
            else:
                col_units.append('')
        return col_units

    def add_to_database(self):
        """Initiate the insertion of data to the database."""
        col_types = self.get_col_types()
        col_units = self.get_col_units()
        prep_data = self.prep_data()
        if not prep_data[0]:
            return
        fields = prep_data[1]
        crops = prep_data[2]
        dates = prep_data[3]
        focus_cols = prep_data[4]
        df = pd.concat(self.tasks)
        success = self.scale_dfs(df)
        if not success[0]:
            return False
        for i, field in enumerate(fields):
            crop = crops[i]
            date = dates[i]
            columns = []
            table = f'{check_text(field)}_{check_text(crop)}_{check_text(date)}'
            for col in df.columns:
                columns.append(check_text(col))
            insert_sql, _ = create_table(self.db, self.data_type, columns, 'latitude', 'longitude', 'time_stamp', '',
                                         col_types, column_units=col_units, table=table, ask_replace=False)
            insert_data(self.tr, self.db, df, self.data_type, insert_sql, table, field, focus_cols, col_types)
        self.close()


def insert_data(tr, db, data: pd.DataFrame, schema: str, insert_sql: str, tbl_name: str, field: str, focus_col: list,
                col_types: list):
    """Makes the actual insertion to the database (first to a temp table and then to the correct table)."""
    sql = insert_sql + '('
    count_db_insert = 0
    for row_nr, row in data.iterrows():
        lat_lon_insert = False
        for col_nr, col in enumerate(data.columns):
            if col in ['latitude', 'longitude']:
                if not lat_lon_insert:
                    sql += f"ST_PointFromText('POINT({row['longitude']} {row['latitude']})', 4326), "
                    lat_lon_insert = True
                continue
            if col == 'time_stamp':
                sql += f"'{row['time_stamp']}', "
                continue
            if str(row[col]) == 'nan':
                sql += f"Null, "
            elif str(row[col]).lower() == 'none':
                sql += f"Null, "
            elif col_types[col_nr] == 2:
                sql += f"'{row[col]}', "
            else:
                sql += f"{row[col]}, "
        sql = sql[:-2] + '), ('
        if count_db_insert > 10000:
            db.execute_sql(sql[:-3], return_failure=True)
            sql = insert_sql + '('
            count_db_insert = 0
        else:
            count_db_insert += 1
    if count_db_insert > 0:
        db.execute_sql(sql[:-3])

    sql = f"""SELECT * INTO {schema}.{tbl_name} 
    from {schema}.temp_table
    where st_intersects(pos, (select polygon 
    from fields where field_name = '{field}'))
    """
    suc = db.execute_sql(sql, return_failure=True, return_row_count=True)
    if not suc[0]:
        return suc
    if suc[2] == 0:
        QtWidgets.QMessageBox.information(None, tr("Warning:"),
                                          tr('No data was found on that field.'))
    if schema != 'harvest':
        create_polygons(db, schema, tbl_name, field)
    db.execute_sql(f"DROP TABLE {schema}.temp_table")
    for col in focus_col:
        db.create_indexes(tbl_name, col, schema, primary_key=False)


class App:
    def __init__(self):
        self.dock_widget = GeoDataFarmDockWidget(None)
        self.db = DB(self.dock_widget)


if __name__ == '__main__':
    test_path = 'c:\\dev\\geodatafarm\\test_data\\TASKDATA\\'
    ap = None
    iso = Iso11783(ap)
    iso.initate_pyagriculture(test_path)
    iso.get_task_names()
