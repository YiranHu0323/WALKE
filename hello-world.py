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

from math import sin, cos
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

class Signals(QObject):
    autotest_complete = pyqtSignal(bool)
    status_update = pyqtSignal(str)
    servo_status = pyqtSignal(int, bool, float, float, float, bool)

class RobotController:
    def __init__(self, port: str, servo_ids: List[int], max_retries: int = 3, retry_delay: float = 1.0):
        self.servos = {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.safe_positions = {
            1: 111,
            2: 120,
            3: 120,
            4: 133,
            5: 120,
            6: 120
        }
        # Temperature and current limits
        self.temp_min = 20  # °C
        self.temp_max = 85  # °C
        self.voltage_min = 6000  # mV
        self.voltage_max = 12000  # mV
        self.position_tolerance = 5

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
                    self.servos[3].move(sin(t) * 30 + 120)
                if 6 in self.servos:
                    self.servos[6].move(cos(t) * 30 + 120)
                time.sleep(0.005)
                t += 0.1
            except ServoTimeoutError as e:
                print(f"Lost communication with servo {e.id_}")
                break
            except KeyboardInterrupt:
                print("\nStopping demo...")
                break

    def safe_shutdown(self) -> tuple[bool, str]:
        """
        Performs a safe shutdown procedure for all servos.
        Returns: (success: bool, message: str)
        """
        try:
            # Query current positions and check motor health
            current_positions = {}
            motor_health = {}
            
            for servo_id, servo in self.servos.items():
                try:
                    servo.enable_torque()
                    time.sleep(0.1)
                    
                    position = servo.get_physical_angle()
                    temp = servo.get_temp()
                    voltage = servo.get_vin()
                    
                    current_positions[servo_id] = position
                    
                    # Check temperature and voltage
                    if temp < self.temp_min or temp > self.temp_max:
                        return False, f"Servo {servo_id} temperature ({temp}°C) out of safe range"
                    if voltage < self.voltage_min or voltage > self.voltage_max:
                        return False, f"Servo {servo_id} voltage ({voltage/1000:.1f}V) out of safe range"
                        
                    motor_health[servo_id] = True
                except (ServoTimeoutError, ServoChecksumError) as e:
                    return False, f"Failed to query servo {servo_id}: {str(e)}"
            
            steps = 20
            increments = {}
            for servo_id in self.servos:
                start_pos = current_positions[servo_id]
                end_pos = self.safe_positions[servo_id]
                increments[servo_id] = (end_pos - start_pos) / steps
            
            # Gradually move to safe position
            for step in range(steps):
                for servo_id, servo in self.servos.items():
                    target = current_positions[servo_id] + increments[servo_id]
                    try:
                        servo.move(target)
                        current_positions[servo_id] = target
                    except (ServoTimeoutError, ServoChecksumError) as e:
                        return False, f"Failed to move servo {servo_id} to safe position: {str(e)}"
                time.sleep(0.1)
            
            # Verify final positions
            for servo_id, servo in self.servos.items():
                try:
                    final_pos = servo.get_physical_angle()
                    if abs(final_pos - self.safe_positions[servo_id]) > self.position_tolerance:
                        return False, f"Servo {servo_id} failed to reach safe position"
                except (ServoTimeoutError, ServoChecksumError) as e:
                    return False, f"Failed to verify servo {servo_id} position: {str(e)}"
            
            # Disable all motors
            for servo_id, servo in self.servos.items():
                try:
                    servo.disable_torque()
                except (ServoTimeoutError, ServoChecksumError) as e:
                    return False, f"Failed to disable servo {servo_id}: {str(e)}"
            
            return True, "Shutdown completed successfully"
            
        except Exception as e:
            return False, f"Unexpected error during shutdown: {str(e)}"

class ServoDataRecorder:
    def __init__(self):
        self.times = []
        self.servo3_positions = []
        self.servo6_positions = []
        self.start_time = None
        self.recording = False
        
    def start(self):
        """Start recording"""
        self.times = []
        self.servo3_positions = []
        self.servo6_positions = []
        self.start_time = time.time()
        self.recording = True
        
    def record(self, servo3_pos, servo6_pos):
        """Record a new data point"""
        if not self.recording:
            return
            
        current_time = time.time() - self.start_time
        self.times.append(current_time)
        self.servo3_positions.append(servo3_pos)
        self.servo6_positions.append(servo6_pos)
        
    def save_plot(self):
        """Save the movement plot"""
        if not self.recording or not self.times:
            return
            
        self.recording = False
        
        # Create the figure
        plt.figure(figsize=(12, 6))
        
        # Plot servo positions
        plt.plot(self.times, self.servo3_positions, 'b-', label='Servo 3', linewidth=2)
        plt.plot(self.times, self.servo6_positions, 'g-', label='Servo 6', linewidth=2)
        
        # Add labels and title
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle (degrees)')
        plt.title('Servo Positions During Demo')
        plt.grid(True)
        plt.legend()
        
        # Set y-axis limits to match servo range
        plt.ylim(0, 240)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'servo_recording_{timestamp}.png'
        
        # Save figure
        plt.savefig(filename)
        plt.close()
        
        print(f"\nRecording saved to {filename}")
        
        # Print statistics
        stats = {
            'Servo 3': {
                'Mean': np.mean(self.servo3_positions),
                'Min': np.min(self.servo3_positions),
                'Max': np.max(self.servo3_positions),
                'Range': np.ptp(self.servo3_positions),
            },
            'Servo 6': {
                'Mean': np.mean(self.servo6_positions),
                'Min': np.min(self.servo6_positions),
                'Max': np.max(self.servo6_positions),
                'Range': np.ptp(self.servo6_positions),
            }
        }
        
        print("\nMovement Statistics:")
        print("-" * 40)
        for servo, data in stats.items():
            print(f"\n{servo}:")
            for stat, value in data.items():
                print(f"{stat}: {value:.2f}°")
        print(f"\nRecording duration: {self.times[-1]:.2f} seconds")

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
        font.setPointSize(16)
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
        status_font.setPointSize(16)
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
            1: 111,  # left hip
            2: 120,  # left lower leg
            3: 120,  # left upper leg
            4: 133,  # right hip
            5: 120,  # right lower leg
            6: 120   # right upper leg
        }

        self.moving_forward = False
        self.moving_sideways = False
        self.sideways_direction = 0  # -1 for left, 1 for right
        self.control_thread = None
        self.t = 0
    
    def setup_control_panel(self):
        control_panel = QWidget()
        panel_layout = QVBoxLayout()
        
        # Create direction buttons
        button_grid = QGridLayout()
        
        self.forward_button = QPushButton("Forward")
        self.left_button = QPushButton("Left")
        self.right_button = QPushButton("Right")
        self.stop_button = QPushButton("Stop")
        
        # Style control buttons
        control_buttons = [self.forward_button, self.left_button, 
                         self.right_button, self.stop_button]
        
        for button in control_buttons:
            button.setMinimumSize(100, 50)
            font = button.font()
            font.setPointSize(16)
            font.setBold(True)
            button.setFont(font)
        
        # Set specific colors for each button
        self.forward_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        
        self.left_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        
        self.right_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        
        # Connect button signals
        self.forward_button.clicked.connect(self.toggle_forward)
        self.left_button.clicked.connect(lambda: self.move_sideways(-1))
        self.right_button.clicked.connect(lambda: self.move_sideways(1))
        self.stop_button.clicked.connect(self.stop_all)
        
        # Arrange buttons in grid
        button_grid.addWidget(self.forward_button, 0, 1)
        button_grid.addWidget(self.left_button, 1, 0)
        button_grid.addWidget(self.stop_button, 1, 1)
        button_grid.addWidget(self.right_button, 1, 2)
        
        panel_layout.addLayout(button_grid)
        control_panel.setLayout(panel_layout)
        
        # Disable control panel initially
        for button in control_buttons:
            button.setEnabled(False)
            
        return control_panel
    
    def toggle_forward(self):
        """Toggle forward movement"""
        if not self.moving_forward:
            # Enable torque first
            with self.robot_wrapper.lock:
                try:
                    if 3 in self.robot.servos:
                        self.robot.servos[3].enable_torque()
                    if 6 in self.robot.servos:
                        self.robot.servos[6].enable_torque()
                    time.sleep(0.1)  # Give time for torque to enable
                except Exception as e:
                    print(f"Error enabling torque: {str(e)}")
                    return
                    
            self.moving_forward = True
            self.forward_button.setText("Stop Forward")
            self.start_control_thread()
        else:
            self.moving_forward = False
            self.forward_button.setText("Forward")
            
    def move_sideways(self, direction):
        """Start sideways movement (-1 for left, 1 for right)"""
        if self.robot and self.robot_wrapper:
            self.sideways_direction = direction
            if not self.moving_sideways:
                # Enable torque first
                with self.robot_wrapper.lock:
                    try:
                        if 1 in self.robot.servos:
                            self.robot.servos[1].enable_torque()
                        if 4 in self.robot.servos:
                            self.robot.servos[4].enable_torque()
                        time.sleep(0.1)  # Give time for torque to enable
                    except Exception as e:
                        print(f"Error enabling torque: {str(e)}")
                        return
                
                self.moving_sideways = True
                if direction < 0:
                    self.left_button.setEnabled(False)
                    self.right_button.setEnabled(True)
                else:
                    self.right_button.setEnabled(False)
                    self.left_button.setEnabled(True)
                self.start_control_thread()
    
    def stop_all(self):
        """Stop all movements"""
        self.moving_forward = False
        self.moving_sideways = False
        self.sideways_direction = 0
        self.forward_button.setText("Forward")
        self.left_button.setEnabled(True)
        self.right_button.setEnabled(True)
        self.t = 0
        
        # Move servos back to home positions
        def reset_thread():
            if self.robot and self.robot_wrapper:
                with self.robot_wrapper.lock:
                    try:
                        # Enable torque for all servos first
                        for servo_id in [1, 3, 4, 6]:
                            if servo_id in self.robot.servos:
                                self.robot.servos[servo_id].enable_torque()
                        time.sleep(0.1)  # Give time for torque to enable
                        
                        # Reset hip servos
                        if 1 in self.robot.servos:
                            self.robot.servos[1].move(self.home_positions[1])
                        if 4 in self.robot.servos:
                            self.robot.servos[4].move(self.home_positions[4])
                        # Reset leg servos
                        if 3 in self.robot.servos:
                            self.robot.servos[3].move(self.home_positions[3])
                        if 6 in self.robot.servos:
                            self.robot.servos[6].move(self.home_positions[6])
                    except Exception as e:
                        print(f"Error resetting servos: {str(e)}")
        
        Thread(target=reset_thread).start()
    
    def start_control_thread(self):
        """Start the control thread if not already running"""
        if self.control_thread is None or not self.control_thread.is_alive():
            self.control_thread = Thread(target=self.control_loop)
            self.control_thread.start()
    
    def control_loop(self):
        """Main control loop for robot movement"""
        while self.moving_forward or self.moving_sideways:
            try:
                with self.robot_wrapper.lock:
                    # Forward movement (servos 3 and 6)
                    if self.moving_forward:
                        if 3 in self.robot.servos:
                            self.robot.servos[3].move(sin(self.t) * 10 + 120)
                        if 6 in self.robot.servos:
                            self.robot.servos[6].move(cos(self.t) * 10 + 120)
                        self.t += 0.1
                    
                    # Sideways movement (servos 1 and 4)
                    if self.moving_sideways:
                        try:
                            # Calculate target positions
                            offset = 10 * self.sideways_direction
                            target1 = self.home_positions[1] + offset
                            target4 = self.home_positions[4] + offset
                            
                            # Move servos gradually
                            if 1 in self.robot.servos:
                                current1 = self.robot.servos[1].get_physical_angle()
                                step1 = (target1 - current1) * 0.1  # Move 10% of remaining distance
                                self.robot.servos[1].move(current1 + step1)
                                
                            if 4 in self.robot.servos:
                                current4 = self.robot.servos[4].get_physical_angle()
                                step4 = (target4 - current4) * 0.1  # Move 10% of remaining distance
                                self.robot.servos[4].move(current4 + step4)
                                
                        except Exception as e:
                            print(f"Sideways movement error: {str(e)}")
                
                time.sleep(0.01)
            except Exception as e:
                print(f"Control loop error: {str(e)}")
                break
    
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

        control_panel = self.setup_control_panel()
        main_layout.addWidget(control_panel)

        self.connect_button = QPushButton("Connect")
        self.test_button = QPushButton("Run Autotest")
        self.demo_button = QPushButton("Start Demo")
        
        # Style all buttons
        for button in [self.connect_button, self.test_button, self.demo_button]:
            button.setMinimumSize(150, 50)  # Make buttons larger
            font = button.font()
            font.setPointSize(16)
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
        status_font.setPointSize(16)
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

            with self.robot_wrapper.lock:
                for servo_id in [1, 3, 4, 6]:
                    if servo_id in self.robot.servos:
                        self.robot.servos[servo_id].enable_torque()

            self.connect_button.setEnabled(False)
            self.test_button.setEnabled(True)
            self.demo_button.setEnabled(True)

            self.forward_button.setEnabled(True)
            self.left_button.setEnabled(True)
            self.right_button.setEnabled(True)
            self.stop_button.setEnabled(True)

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
                    
                    # self.signals.status_update.emit("LED celebration completed!")
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
            self.recorder = ServoDataRecorder()
            self.recorder.start()

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
                            if 3 in self.robot.servos and 6 in self.robot.servos:
                                # Get current positions
                                servo3_pos = self.robot.servos[3].get_physical_angle()
                                servo6_pos = self.robot.servos[6].get_physical_angle()
                                
                                # Record positions
                                self.recorder.record(servo3_pos, servo6_pos)
                                
                                # Move servos
                                self.robot.servos[3].move(sin(t) * 10 + 120)
                                self.robot.servos[6].move(cos(t) * 10 + 120)

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
                
                if self.recorder:
                    self.recorder.save_plot()

                # Safe shutdown after demo stops
                if self.robot and self.robot_wrapper:
                    with self.robot_wrapper.lock:
                        success, message = self.robot.safe_shutdown()
                        self.signals.status_update.emit(f"Shutdown status: {message}")

                        for servo_id in [3, 6]:
                            if servo_id in self.robot.servos:
                                try:
                                    self.robot.servos[servo_id].enable_torque()
                                except:
                                    pass

                # Update UI from thread
                if not self.running:
                    self.signals.status_update.emit("Demo stopped")
                    # Reset button state
                    self.demo_button.setText("Start Demo")
                    self.test_button.setEnabled(True)
            
            self.demo_thread = Thread(target=demo_thread)
            self.demo_thread.start()
            self.signals.status_update.emit("Demo running...")
        else:
            self.running = False
            if self.recorder:
                self.recorder.save_plot()
            self.demo_button.setText("Start Demo")
            self.test_button.setEnabled(True)
            self.signals.status_update.emit("Stopping demo and performing safe shutdown...")

            def shutdown_thread():
                if self.robot and self.robot_wrapper:
                    with self.robot_wrapper.lock:
                        success, message = self.robot.safe_shutdown()
                        self.signals.status_update.emit(f"Shutdown status: {message}")
                        
                        # Re-enable torque after shutdown
                        for servo_id in [3, 6]:  # Only for demo servos
                            if servo_id in self.robot.servos:
                                try:
                                    self.robot.servos[servo_id].enable_torque()
                                except:
                                    pass
            
            Thread(target=shutdown_thread).start()

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
                # for servo in self.robot.servos.values():
                #     try:
                #         servo.disable_torque()
                #     except:
                #         pass
                success, message = self.robot.safe_shutdown()
                print(f"Final shutdown status: {message}")
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ServoControlGUI()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()