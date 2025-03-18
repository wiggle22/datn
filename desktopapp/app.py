import sys
import serial
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QMessageBox, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, Qt

class SerialThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True

    def run(self):
        ser = serial.Serial(self.port, self.baudrate)
        while self.running:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                self.data_received.emit(line)

    def stop(self):
        self.running = False
        self.wait()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.recorded_data = {}  # Dictionary để lưu dữ liệu đã nhận

    def initUI(self):
        self.setWindowTitle('RFID Parking System')
        self.setGeometry(100, 100, 1200, 800)

        # Layout chính
        main_layout = QHBoxLayout()
        
        # Layout làn vào
        lane_in_layout = QVBoxLayout()
        lane_in_group = QGroupBox("Làn Vào")
        lane_in_group.setStyleSheet("font-size: 18px;")
        
        self.lane_in_info_label = QLabel("THÔNG TIN XE VÀO")
        self.lane_in_info_label.setAlignment(Qt.AlignCenter)
        self.lane_in_info_label.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 20px;")
        lane_in_layout.addWidget(self.lane_in_info_label)

        self.lane_in_uid_label = QLabel("UID: ")
        self.lane_in_uid_label.setStyleSheet("font-size: 30px;")
        self.lane_in_time_label = QLabel("Giờ Vào: ")
        self.lane_in_time_label.setStyleSheet("font-size: 30px;")
        
        lane_in_layout.addWidget(self.lane_in_uid_label)
        lane_in_layout.addWidget(self.lane_in_time_label)
        
        lane_in_group.setLayout(lane_in_layout)

        # Layout làn ra
        lane_out_layout = QVBoxLayout()
        lane_out_group = QGroupBox("Làn Ra")
        lane_out_group.setStyleSheet("font-size: 18px;")
        
        self.lane_out_info_label = QLabel("THÔNG TIN XE RA")
        self.lane_out_info_label.setAlignment(Qt.AlignCenter)
        self.lane_out_info_label.setStyleSheet("background-color: green; color: white; font-weight: bold; font-size: 20px;")
        lane_out_layout.addWidget(self.lane_out_info_label)

        self.lane_out_uid_label = QLabel("UID: ")
        self.lane_out_uid_label.setStyleSheet("font-size: 30px;")
        self.lane_out_entry_time_label = QLabel("Giờ Vào: ")
        self.lane_out_entry_time_label.setStyleSheet("font-size: 30px;")
        self.lane_out_exit_time_label = QLabel("Giờ Ra: ")
        self.lane_out_exit_time_label.setStyleSheet("font-size: 30px;")
        self.lane_out_fee_label = QLabel("Phí gửi xe: ")
        self.lane_out_fee_label.setStyleSheet("font-size: 30px;")
        
        lane_out_layout.addWidget(self.lane_out_uid_label)
        lane_out_layout.addWidget(self.lane_out_entry_time_label)
        lane_out_layout.addWidget(self.lane_out_exit_time_label)
        lane_out_layout.addWidget(self.lane_out_fee_label)
        
        lane_out_group.setLayout(lane_out_layout)

        # Đặt tỷ lệ cho các phần
        lane_in_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lane_out_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Thêm vào main layout
        main_layout.addWidget(lane_in_group, 4)
        main_layout.addWidget(lane_out_group, 6)

        self.setLayout(main_layout)

        # Thiết lập Serial Thread
        self.serial_thread = SerialThread('COM8', 115200)  # Thay đổi cổng và baudrate nếu cần
        self.serial_thread.data_received.connect(self.update_ui)
        self.serial_thread.start()

    def update_ui(self, data):
        print(data)
        # Phân tích dữ liệu và cập nhật giao diện người dùng
        if 'Card UID' in data:
            self.recorded_data = {}  # Reset dictionary khi nhận dữ liệu mới
            uid = data.split(': ')[1] if len(data.split(': ')) > 1 else ""
            self.recorded_data['uid'] = uid
        elif 'Entry recorded' in data:
            self.recorded_data['status'] = 'entry'
        elif 'Exit recorded' in data:
            self.recorded_data['status'] = 'exit'
        elif 'Entry time' in data:
            entry_time = data.split(': ')[1] if len(data.split(': ')) > 1 else ""
            self.recorded_data['entry_time'] = entry_time
        elif 'Exit time' in data:
            exit_time = data.split(': ')[1] if len(data.split(': ')) > 1 else ""
            self.recorded_data['exit_time'] = exit_time
        elif 'Rfid code' in data:
            rfid_code = data.split(': ')[1] if len(data.split(': ')) > 1 else ""
            self.recorded_data['rfid_code'] = rfid_code
        elif 'Fee' in data:
            fee = data.split(': ')[1].split(' ')[0] if len(data.split(': ')) > 1 else ""
            self.recorded_data['fee'] = fee
        elif 'Lot not available, gate will not open' in data:
            self.recorded_data['status'] = 'lot not available'
        elif 'Entry already recorded, gate will not open' in data:
            self.recorded_data['status'] = 'entry already recorded'
        elif 'No entry record found, gate will not open' in data:
            self.recorded_data['status'] = 'no entry record found'
        elif 'You dont have permission to entry' in data:
            self.recorded_data['status'] = 'you dont have permission to entry'

        self.update_labels()

    def update_labels(self):
        if 'status' in self.recorded_data:
            if self.recorded_data['status'] == 'entry':
                if 'entry_time' in self.recorded_data:
                    self.lane_in_time_label.setText(f'Giờ Vào: {self.recorded_data["entry_time"]}')
                if 'uid' in self.recorded_data:
                    self.lane_in_uid_label.setText(f'UID: {self.recorded_data["uid"]}')
            elif self.recorded_data['status'] == 'exit':
                if 'uid' in self.recorded_data:
                    self.lane_out_uid_label.setText(f'UID: {self.recorded_data["uid"]}')
                if 'entry_time' in self.recorded_data:
                    self.lane_out_entry_time_label.setText(f'Giờ Vào: {self.recorded_data["entry_time"]}')
                if 'exit_time' in self.recorded_data:
                    self.lane_out_exit_time_label.setText(f'Giờ Ra: {self.recorded_data["exit_time"]}')
                if 'fee' in self.recorded_data:
                    self.lane_out_fee_label.setText(f'Phí gửi xe: {self.recorded_data["fee"]} VNĐ')
            elif self.recorded_data['status'] == 'lot not available':
                self.show_message("Lot not available, gate will not open")
            elif self.recorded_data['status'] == 'entry already recorded':
                self.show_message("Entry already recorded, gate will not open")
            elif self.recorded_data['status'] == 'no entry record found':
                self.show_message("No entry record found, gate will not open")
            elif self.recorded_data['status'] == 'you dont have permission to entry':
                self.show_message("You dont have permission to entry")

    def show_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
