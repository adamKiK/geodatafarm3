from ..import_data.handle_text_data import InputTextHandler
from ..import_data.handle_input_shp_data import InputShpHandler
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QDate
from ..support_scripts.__init__ import TR


class SaveHarvesting:
    def __init__(self, parent):
        """
        A class for storing harvesting data
        Parameters
        ----------
        parent: GeoDataFarm
        """
        self.dw = parent.dock_widget
        translate = TR('SaveHarvesting')
        self.tr = translate.tr
        self.parent = parent

    def set_widget_connections(self):
        """A simple function that sets the buttons on the planting tab"""
        self.parent.dock_widget.PBHvAddFile.clicked.connect(self.run_file_import)
        self.parent.dock_widget.PBHvSaveManual.clicked.connect(self.save_manual_data)

    def run_file_import(self):
        """The function loads the correct import dialog for files"""
        columns = [self.tr('Yield'), self.tr('Total yield')]
        if self.dw.CBHvFileType.currentText() == self.tr('Text file (.csv; .txt)'):
            add_f = InputTextHandler(self.parent, 'harvest', columns=columns)
            add_f.run()
        elif self.dw.CBHvFileType.currentText() == self.tr('Databasefile (.db)'):
            QMessageBox.information(None, "Error:", self.tr(
                'Support for databasefiles are not implemented 100% yet'))
            return
            self.IH = dbFileHandler(self.iface, self.dock_widget)
            self.IH.start_up()
        elif self.dw.CBHvFileType.currentText() == self.tr('Shape file (.shp)'):
            shp_file = InputShpHandler(self.parent, 'harvest', columns)
            shp_file.run()

    def save_manual_data(self):
        """Saves the manual data."""
        if self.check_input():
            field = self.dw.CBHvField.currentText()
            crop = self.dw.CBHvCrop.currentText()
            date_ = self.dw.DEHarvesting.text()
            total_yield = self.dw.LEHvTotalYield.text()
            yield_ = self.dw.LEHvTotalYield.text()
            other = self.dw.LEHvOther.toPlainText()
            if total_yield == '':
                total_yield = 'Null'
            if yield_ == '':
                yield_ = 'Null'
            if other == '':
                other = 'Null'
            sql = """Insert into harvest.manual(field, crop, date_, total_yield, yield, other, table_) 
            VALUES ('{field}', '{crop}', '{date_}','{total_yield}','{yield_}','{other}', 'None')
            """.format(field=field, crop=crop, date_=date_, total_yield=total_yield, yield_=yield_, other=other)
            try:
                self.parent.db.execute_sql(sql)
                QMessageBox.information(None, self.tr('Success'), self.tr('The data was stored correctly'))
            except Exception as e:
                QMessageBox.information(None, self.tr('Error'),
                                        self.tr('Following error occurred: {m}'.format(m=e)))
        self.reset_widget()

    def reset_widget(self):
        """Resets the widget to the default values"""
        self.dw.CBHvField.setCurrentIndex(0)
        self.dw.CBHvCrop.setCurrentIndex(0)
        self.dw.DEHarvesting.setDate(QDate.fromString('2000-01-01', 'yyyy-MM-dd'))
        self.dw.LEHvTotalYield.setText('')
        self.dw.LEHvYield.setText('')
        self.dw.LEHvOther.setPlainText('')

    def check_input(self):
        """Some simple checks that ensure that the basic data is filled in.

        Returns
        -------
        bool
        """
        if self.dw.CBHvField.currentText() == self.tr('--- Select field ---'):
            QMessageBox.information(None, self.tr('Error:'), self.tr('In order to save the data you must select a field'))
            return False
        if self.dw.CBHvCrop.currentText() == self.tr('--- Select crop ---'):
            QMessageBox.information(None, self.tr('Error:'), self.tr('In order to save the data you must select a crop'))
            return False
        if self.dw.DEHvraying.text() == '2000-01-01':
            QMessageBox.information(None, self.tr('Error:'), self.tr('In order to save the data you must select a date'))
            return False
        return True
