# from math import sin, cos
# from pylx16a.lx16a import *
# import time

# LX16A.initialize("COM4", 0.1)

# try:
#     servo1 = LX16A(3)
#     servo2 = LX16A(6)
#     servo1.set_angle_limits(0, 240)
#     servo2.set_angle_limits(0, 240)
# except ServoTimeoutError as e:
#     print(f"Servo {e.id_} is not responding. Exiting...")
#     quit()

# t = 0
# while True:
#     servo1.move(sin(t) * 10 + 160)
#     servo2.move(cos(t) * 10 + 100)

#     time.sleep(0.01)
#     t += 0.1

# from math import sin, cos
# from typing import List
# from pylx16a.lx16a import *
# import time

# class RobotController:
#     def __init__(self, port: str, servo_ids: List[int], max_retries: int = 3, retry_delay: float = 1.0):
#         self.servos = {}
#         self.max_retries = max_retries
#         self.retry_delay = retry_delay
#         LX16A.initialize(port, 0.1)
#         self._setup_servos(servo_ids)

#     def _try_connect_servo(self, id: int) -> LX16A:
#         """Attempt to connect to a servo with retries"""
#         attempts = 0
#         while attempts < self.max_retries:
#             try:
#                 servo = LX16A(id)
#                 servo.set_angle_limits(0, 240)
#                 print(f"Successfully connected to servo {id}")
#                 return servo
#             except ServoTimeoutError:
#                 attempts += 1
#                 print(f"Attempt {attempts}/{self.max_retries} failed for servo {id}")
#                 if attempts < self.max_retries:
#                     print(f"Retrying in {self.retry_delay} seconds...")
#                     time.sleep(self.retry_delay)
        
#         raise ServoTimeoutError(f"Failed to connect to servo {id} after {self.max_retries} attempts", id)

#     def _setup_servos(self, servo_ids: List[int]):
#         failed_servos = []
#         for id in servo_ids:
#             try:
#                 servo = self._try_connect_servo(id)
#                 self.servos[id] = servo
#             except ServoTimeoutError as e:
#                 print(f"Warning: Failed to initialize servo {id} after all attempts")
#                 failed_servos.append(id)

#         if failed_servos:
#             print(f"\nFailed to connect to the following servos: {failed_servos}")
#             response = input("Do you want to continue anyway? (y/n): ")
#             if response.lower() != 'y':
#                 raise Exception("Setup aborted by user")

#     def run_autotest(self):
#         print("Starting autotest procedure...")
        
#         # Test communication and query positions
#         for id, servo in self.servos.items():
#             attempts = 0
#             while attempts < self.max_retries:
#                 try:
#                     angle = servo.get_physical_angle()
#                     print(f"Servo {id} position: {angle:.2f} degrees")
#                     break
#                 except ServoTimeoutError:
#                     attempts += 1
#                     if attempts == self.max_retries:
#                         print(f"ERROR: Cannot communicate with servo {id} after {self.max_retries} attempts")
#                         return False
#                     print(f"Retry {attempts}/{self.max_retries} for servo {id}")
#                     time.sleep(self.retry_delay)

#         # Test power levels
#         for id, servo in self.servos.items():
#             attempts = 0
#             while attempts < self.max_retries:
#                 try:
#                     voltage = servo.get_vin()
#                     print(f"Servo {id} voltage: {voltage/1000:.2f}V")
#                     if voltage < 6000:  # 6V minimum
#                         print(f"ERROR: Servo {id} voltage too low")
#                         return False
#                     break
#                 except ServoTimeoutError:
#                     attempts += 1
#                     if attempts == self.max_retries:
#                         print(f"ERROR: Cannot read voltage from servo {id} after {self.max_retries} attempts")
#                         return False
#                     print(f"Retry {attempts}/{self.max_retries} for servo {id}")
#                     time.sleep(self.retry_delay)

#         # Test torque enable/disable
#         for id, servo in self.servos.items():
#             attempts = 0
#             while attempts < self.max_retries:
#                 try:
#                     servo.disable_torque()
#                     if servo.is_torque_enabled():
#                         print(f"ERROR: Failed to disable torque on servo {id}")
#                         return False
#                     servo.enable_torque()
#                     if not servo.is_torque_enabled():
#                         print(f"ERROR: Failed to enable torque on servo {id}")
#                         return False
#                     break
#                 except ServoTimeoutError:
#                     attempts += 1
#                     if attempts == self.max_retries:
#                         print(f"ERROR: Cannot control torque on servo {id} after {self.max_retries} attempts")
#                         return False
#                     print(f"Retry {attempts}/{self.max_retries} for servo {id}")
#                     time.sleep(self.retry_delay)

#         # Flash LEDs
#         for _ in range(3):
#             for servo in self.servos.values():
#                 try:
#                     servo.led_power_on()
#                 except ServoTimeoutError:
#                     continue
#             time.sleep(0.5)
#             for servo in self.servos.values():
#                 try:
#                     servo.led_power_off()
#                 except ServoTimeoutError:
#                     continue
#             time.sleep(0.5)

#         print("Autotest completed successfully")
#         return True

#     def run_demo(self):
#         t = 0
#         while True:
#             try:
#                 # Only move servos 3 and 6 (upper legs)
#                 if 3 in self.servos:
#                     self.servos[3].move(sin(t) * 10 + 160)
#                 if 6 in self.servos:
#                     self.servos[6].move(cos(t) * 10 + 100)
#                 time.sleep(0.01)
#                 t += 0.1
#             except ServoTimeoutError as e:
#                 print(f"Lost communication with servo {e.id_}")
#                 break
#             except KeyboardInterrupt:
#                 print("\nStopping demo...")
#                 break

# def main():
#     try:
#         # Initialize robot with all 6 servos, 3 retry attempts, 1 second between retries
#         robot = RobotController("COM4", [1, 2, 3, 4, 5, 6], max_retries=3, retry_delay=1.0)
        
#         # Run autotest first
#         if not robot.run_autotest():
#             print("Autotest failed, exiting...")
#             return
        
#         # If autotest passes, run the demo
#         print("\nStarting demo motion...")
#         robot.run_demo()
        
#     except ServoTimeoutError as e:
#         print(f"Failed to initialize servo {e.id_}. Please check connections.")
#     except serial.SerialException:
#         print("Failed to open serial port. Please check port name and connections.")
#     except Exception as e:
#         print(f"Unexpected error: {str(e)}")

# if __name__ == "__main__":
#     main()

from math import sin, cos
from typing import List
import sys
import time
from threading import Thread, Lock
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QGridLayout, 
                           QStatusBar, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QColor
from pylx16a.lx16a import *
import serial

class Signals(QObject):
    autotest_complete = pyqtSignal(bool)
    status_update = pyqtSignal(str)
    servo_status = pyqtSignal(int, bool, float, float, float, bool)

class RobotController:
    def __init__(self, port: str, servo_ids: List[int], max_retries: int = 3, retry_delay: float = 1.0):
        self.servos = {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        LX16A.initialize(port, 0.1)
        self._setup_servos(servo_ids)

    def _try_connect_servo(self, id: int) -> LX16A:
        """Attempt to connect to a servo with retries"""
        attempts = 0
        while attempts < self.max_retries:
            try:
                servo = LX16A(id)
                servo.set_angle_limits(0, 240)
                print(f"Successfully connected to servo {id}")
                return servo
            except ServoTimeoutError:
                attempts += 1
                print(f"Attempt {attempts}/{self.max_retries} failed for servo {id}")
                if attempts < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
        
        raise ServoTimeoutError(f"Failed to connect to servo {id} after {self.max_retries} attempts", id)

    def _setup_servos(self, servo_ids: List[int]):
        failed_servos = []
        for id in servo_ids:
            try:
                servo = self._try_connect_servo(id)
                self.servos[id] = servo
            except ServoTimeoutError as e:
                print(f"Warning: Failed to initialize servo {id} after all attempts")
                failed_servos.append(id)

        if failed_servos:
            print(f"\nFailed to connect to the following servos: {failed_servos}")
            response = input("Do you want to continue anyway? (y/n): ")
            if response.lower() != 'y':
                raise Exception("Setup aborted by user")

    def run_autotest(self):
        print("Starting autotest procedure...")
        
        # Test communication and query positions
        for id, servo in self.servos.items():
            attempts = 0
            while attempts < self.max_retries:
                try:
                    angle = servo.get_physical_angle()
                    print(f"Servo {id} position: {angle:.2f} degrees")
                    break
                except ServoTimeoutError:
                    attempts += 1
                    if attempts == self.max_retries:
                        print(f"ERROR: Cannot communicate with servo {id} after {self.max_retries} attempts")
                        return False
                    print(f"Retry {attempts}/{self.max_retries} for servo {id}")
                    time.sleep(self.retry_delay)

        # Test power levels
        for id, servo in self.servos.items():
            attempts = 0
            while attempts < self.max_retries:
                try:
                    voltage = servo.get_vin()
                    print(f"Servo {id} voltage: {voltage/1000:.2f}V")
                    if voltage < 6000:  # 6V minimum
                        print(f"ERROR: Servo {id} voltage too low")
                        return False
                    break
                except ServoTimeoutError:
                    attempts += 1
                    if attempts == self.max_retries:
                        print(f"ERROR: Cannot read voltage from servo {id} after {self.max_retries} attempts")
                        return False
                    print(f"Retry {attempts}/{self.max_retries} for servo {id}")
                    time.sleep(self.retry_delay)

        # Test torque enable/disable
        for id, servo in self.servos.items():
            attempts = 0
            while attempts < self.max_retries:
                try:
                    servo.disable_torque()
                    if servo.is_torque_enabled():
                        print(f"ERROR: Failed to disable torque on servo {id}")
                        return False
                    servo.enable_torque()
                    if not servo.is_torque_enabled():
                        print(f"ERROR: Failed to enable torque on servo {id}")
                        return False
                    break
                except ServoTimeoutError:
                    attempts += 1
                    if attempts == self.max_retries:
                        print(f"ERROR: Cannot control torque on servo {id} after {self.max_retries} attempts")
                        return False
                    print(f"Retry {attempts}/{self.max_retries} for servo {id}")
                    time.sleep(self.retry_delay)

        # Flash LEDs
        for _ in range(3):
            for servo in self.servos.values():
                try:
                    servo.led_power_on()
                except ServoTimeoutError:
                    continue
            time.sleep(0.5)
            for servo in self.servos.values():
                try:
                    servo.led_power_off()
                except ServoTimeoutError:
                    continue
            time.sleep(0.5)

        print("Autotest completed successfully")
        return True

    def run_demo(self):
        t = 0
        while True:
            try:
                # Only move servos 3 and 6 (upper legs)
                if 3 in self.servos:
                    self.servos[3].move(sin(t) * 10 + 160)
                if 6 in self.servos:
                    self.servos[6].move(cos(t) * 10 + 100)
                time.sleep(0.01)
                t += 0.1
            except ServoTimeoutError as e:
                print(f"Lost communication with servo {e.id_}")
                break
            except KeyboardInterrupt:
                print("\nStopping demo...")
                break

class ServoStatusWidget(QWidget):
    def __init__(self, servo_id: int, parent=None):
        super().__init__(parent)
        self.servo_id = servo_id
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Servo {self.servo_id}")
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status indicators
        self.connection_status = QLabel("Status: Disconnected")
        self.angle_label = QLabel("Angle: --")
        self.voltage_label = QLabel("Voltage: --")
        self.temperature_label = QLabel("Temp: --")
        self.led_indicator = QLabel("LED: OFF")
        
        status_font = font
        status_font.setPointSize(14)
        status_font.setBold(False)
        
        for label in [self.connection_status, self.angle_label, 
                     self.voltage_label, self.temperature_label,
                     self.led_indicator]:
            label.setFont(status_font)
            layout.addWidget(label)
        
        self.setLayout(layout)
        
    def update_status(self, connected: bool, angle: float = None, 
                     voltage: float = None, temp: float = None, led_on: bool = False):
        # self.connection_status.setText(f"Status: {'Connected' if connected else 'Disconnected'}")
        # if connected:
        #     self.angle_label.setText(f"Angle: {angle:.2f}°")
        #     self.voltage_label.setText(f"Voltage: {voltage/1000:.2f}V")
        #     self.temperature_label.setText(f"Temp: {temp}°C")
        #     self.led_indicator.setText(f"LED: {'ON' if led_on else 'OFF'}")
        # else:
        #     self.angle_label.setText("Angle: --")
        #     self.voltage_label.setText("Voltage: --")
        #     self.temperature_label.setText("Temp: --")
        #     self.led_indicator.setText("LED: --")
        status_color = QColor(0, 155, 0) if connected else QColor(155, 0, 0)
        status_text = f"Status: {'Connected' if connected else 'Disconnected'}"
        self.connection_status.setText(status_text)
        self.connection_status.setStyleSheet(f"color: {status_color.name()}")
        
        if connected:
            self.angle_label.setText(f"Angle: {angle:.2f}°")
            self.voltage_label.setText(f"Voltage: {voltage/1000:.2f}V")
            self.temperature_label.setText(f"Temp: {temp}°C")
            self.led_indicator.setText(f"LED: {'ON' if led_on else 'OFF'}")
        else:
            self.angle_label.setText("Angle: --")
            self.voltage_label.setText("Voltage: --")
            self.temperature_label.setText("Temp: --")
            self.led_indicator.setText("LED: --")

class ThreadSafeRobotController:
    def __init__(self, controller):
        self.controller = controller
        self.lock = Lock()
        
    def safe_command(self, func, *args, **kwargs):
        with self.lock:
            try:
                return func(*args, **kwargs)
            except (ServoTimeoutError, serial.SerialTimeoutException) as e:
                print(f"Command failed: {str(e)}")
                return None
            
class ServoControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Servo Control")
        self.robot = None
        self.robot_wrapper = None
        self.demo_thread = None
        self.running = False
        self.signals = Signals()
        self.signals.autotest_complete.connect(self.on_autotest_complete)
        self.signals.status_update.connect(self.update_status_message)
        self.signals.servo_status.connect(self.update_servo_widget)
        self.demo_update_rate = 0.01  # How often to update servo positions (seconds)
        self.status_update_rate = 500  # How often to update status display (milliseconds)
        self.movement_scale = 0.2  # How fast the sine/cosine wave changes
        self.setup_ui()
        self.home_positions = {
            1: 85,  # left hip
            2: 162,  # left lower leg
            3: 160,  # left upper leg
            4: 130,  # right hip
            5: 92,  # right lower leg
            6: 100   # right upper leg
        }
        
    def move_to_home(self):
        """Move all servos to their home positions"""
        if not self.robot or not self.robot_wrapper:
            return False
        
        try:
            with self.robot_wrapper.lock:
                for servo_id, position in self.home_positions.items():
                    if servo_id in self.robot.servos:
                        retry_count = 0
                        max_retries = 3
                        while retry_count < max_retries:
                            try:
                                self.robot.servos[servo_id].move(position)
                                time.sleep(0.2)  # Increased delay to ensure movement completes
                                # Verify position
                                current_pos = self.robot.servos[servo_id].get_physical_angle()
                                if abs(current_pos - position) <= 5:  # 5 degree tolerance
                                    break
                                retry_count += 1
                            except (ServoTimeoutError, ServoChecksumError) as e:
                                print(f"Error homing servo {servo_id} (attempt {retry_count + 1}): {str(e)}")
                                retry_count += 1
                                time.sleep(0.1)
                        
                        if retry_count >= max_retries:
                            print(f"Failed to home servo {servo_id} after {max_retries} attempts")
                            return False
                return True
        except Exception as e:
            print(f"Error during homing: {str(e)}")
            return False
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()

        self.connect_button = QPushButton("Connect")
        self.test_button = QPushButton("Run Autotest")
        self.demo_button = QPushButton("Start Demo")
        
        # Style all buttons
        for button in [self.connect_button, self.test_button, self.demo_button]:
            button.setMinimumSize(150, 50)  # Make buttons larger
            font = button.font()
            font.setPointSize(14)
            font.setBold(True)
            button.setFont(font)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 5px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:disabled {
                    background-color: #BDBDBD;
                }
            """)
        
        self.connect_button.clicked.connect(self.connect_robot)
        self.test_button.clicked.connect(self.run_autotest)
        self.demo_button.clicked.connect(self.toggle_demo)
        
        self.test_button.setEnabled(False)
        self.demo_button.setEnabled(False)
        
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.demo_button)
        main_layout.addLayout(button_layout)
        
        # Servo status grid
        grid_layout = QGridLayout()
        self.servo_widgets = {}
        positions = [(i // 3, i % 3) for i in range(6)]
        
        for pos, servo_id in zip(positions, range(1, 7)):
            widget = ServoStatusWidget(servo_id)
            self.servo_widgets[servo_id] = widget
            grid_layout.addWidget(widget, *pos)
        
        main_layout.addLayout(grid_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        status_font = self.status_bar.font()
        status_font.setPointSize(14)
        self.status_bar.setFont(status_font)
        self.setStatusBar(self.status_bar)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_servo_status)
        self.update_timer.start(self.status_update_rate)

    def connect_robot(self):
        try:
            self.robot = RobotController("/dev/ttyUSB0", list(range(1, 7)), max_retries=3, retry_delay=1.0)
            self.robot_wrapper = ThreadSafeRobotController(self.robot)
            self.connect_button.setEnabled(False)
            self.test_button.setEnabled(True)
            self.demo_button.setEnabled(True)
            self.status_bar.showMessage("Robot connected successfully")
        except Exception as e:
            self.status_bar.showMessage(f"Connection failed: {str(e)}")

    def run_autotest(self):
        if self.robot and self.robot_wrapper:
            self.test_button.setEnabled(False)
            self.demo_button.setEnabled(False)
            
            def test_thread():
                try:
                    with self.robot_wrapper.lock:
                        success = self.robot.run_autotest()
                    self.signals.autotest_complete.emit(success)
                except Exception as e:
                    self.signals.status_update.emit(f"Autotest error: {str(e)}")
                    self.signals.autotest_complete.emit(False)
            
            Thread(target=test_thread).start()
            self.signals.status_update.emit("Running autotest...")

    def flash_leds_celebration(self):
        """Flash LEDs in a celebration pattern after successful tests"""
        def celebration_thread():
            if not self.robot or not self.robot_wrapper:
                return
            
            try:
                with self.robot_wrapper.lock:
                    # Flash LEDs 3 times
                    for _ in range(3):
                        # Turn on LEDs
                        for servo in self.robot.servos.values():
                            try:
                                servo.led_power_on()
                            except ServoTimeoutError:
                                continue
                        time.sleep(0.5)
                        
                        # Turn off LEDs
                        for servo in self.robot.servos.values():
                            try:
                                servo.led_power_off()
                            except ServoTimeoutError:
                                continue
                        time.sleep(0.5)
                    
                    self.signals.status_update.emit("LED celebration completed!")
            except Exception as e:
                self.signals.status_update.emit(f"LED celebration error: {str(e)}")
        
        # Start celebration in separate thread
        Thread(target=celebration_thread).start()

    def on_autotest_complete(self, success: bool):
        if success:
            # Start a new thread for homing to avoid GUI freezing
            def home_thread():
                home_success = self.move_to_home()
                if home_success:
                    self.signals.status_update.emit("Homing completed successfully")
                    self.flash_leds_celebration()
                else:
                    self.signals.status_update.emit("Homing failed")
                # Re-enable buttons after everything is done
                self.test_button.setEnabled(True)
                self.demo_button.setEnabled(True)
            
            self.signals.status_update.emit("Autotest successful, moving to home position...")
            Thread(target=home_thread).start()
        else:
            self.signals.status_update.emit("Autotest failed")
            self.test_button.setEnabled(True)
            self.demo_button.setEnabled(True)

    def update_status_message(self, message: str):
        self.status_bar.showMessage(message)

    def update_servo_status(self):
        if not self.robot or not self.robot_wrapper:
            return
                
        for servo_id, widget in self.servo_widgets.items():
            if servo_id in self.robot.servos:
                servo = self.robot.servos[servo_id]
                try:
                    with self.robot_wrapper.lock:
                        # Add delay between commands to prevent interference
                        angle = servo.get_physical_angle()
                        time.sleep(0.005)
                        voltage = servo.get_vin()
                        time.sleep(0.005)
                        temp = servo.get_temp()
                        time.sleep(0.005)
                        led_on = servo.is_led_power_on()
                    self.signals.servo_status.emit(servo_id, True, angle, voltage, temp, led_on)
                except (ServoTimeoutError, ServoChecksumError, serial.SerialTimeoutException) as e:
                    print(f"Error reading servo {servo_id} status: {str(e)}")
                    self.signals.servo_status.emit(servo_id, False, 0, 0, 0, False)
                except Exception as e:
                    print(f"Unexpected error reading servo {servo_id} status: {str(e)}")
                    self.signals.servo_status.emit(servo_id, False, 0, 0, 0, False)
            else:
                self.signals.servo_status.emit(servo_id, False, 0, 0, 0, False)

    def toggle_demo(self):
        if not self.running:
            self.running = True
            self.demo_button.setText("Stop Demo")
            self.test_button.setEnabled(False)
            
            def demo_thread():
                t = 0
                error_count = 0
                max_errors = 5  # Maximum number of consecutive errors before stopping
                
                while self.running and error_count < max_errors:
                    try:
                        with self.robot_wrapper.lock:
                            if 3 in self.robot.servos:
                                self.robot.servos[3].move(sin(t) * 10 + 160)
                            if 6 in self.robot.servos:
                                self.robot.servos[6].move(cos(t) * 10 + 100)
                        error_count = 0  # Reset error count on successful operation
                        time.sleep(self.demo_update_rate)
                        t += self.movement_scale
                    except (ServoTimeoutError, ServoChecksumError) as e:
                        error_count += 1
                        print(f"Demo error ({error_count}/{max_errors}): {str(e)}")
                        time.sleep(0.05)
                        if error_count >= max_errors:
                            self.signals.status_update.emit(f"Demo stopped due to repeated errors: {str(e)}")
                            self.running = False
                    except Exception as e:
                        self.signals.status_update.emit(f"Unexpected demo error: {str(e)}")
                        self.running = False
                        break

                if error_count >= max_errors:
                    self.running = False
                
                # Update UI from thread
                if not self.running:
                    self.signals.status_update.emit("Demo stopped due to errors")
                    # Reset button state
                    self.demo_button.setText("Start Demo")
                    self.test_button.setEnabled(True)
            
            self.demo_thread = Thread(target=demo_thread)
            self.demo_thread.start()
            self.signals.status_update.emit("Demo running...")
        else:
            self.running = False
            self.demo_button.setText("Start Demo")
            self.test_button.setEnabled(True)
            self.signals.status_update.emit("Demo stopped")

    def update_servo_widget(self, servo_id, connected, angle, voltage, temp, led_on):
        if servo_id in self.servo_widgets:
            self.servo_widgets[servo_id].update_status(connected, angle, voltage, temp, led_on)

    def closeEvent(self, event):
        self.running = False
        if self.demo_thread and self.demo_thread.is_alive():
            self.demo_thread.join()
        if self.robot:
            # Safely stop all servos
            with self.robot_wrapper.lock:
                for servo in self.robot.servos.values():
                    try:
                        servo.disable_torque()
                    except:
                        pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ServoControlGUI()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()