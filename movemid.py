import serial.tools.list_ports
from pylx16a.lx16a import *
import time

def move_all_servos_to_120():
    # Find the first available port
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found!")
        return
    
    # Initialize using the first available port
    port = ports[0].device
    print(f"Using port: {port}")
    
    try:
        # Initialize the bus                               
        LX16A.initialize(port)
        
        # Scan for servos (IDs 0-6)
        found_servos = []
        for servo_id in range(7):
            try:
                servo = LX16A(servo_id)
                found_servos.append(servo)
                print(f"Found servo with ID: {servo_id}")
            except ServoTimeoutError:
                continue
            except Exception as e:
                print(f"Error checking ID {servo_id}: {str(e)}")
        
        if not found_servos:
            print("No servos found!")
            return
            
        print(f"\nMoving {len(found_servos)} servos to 120 degrees...")
        
        # Move all found servos to 120 degrees
        for servo in found_servos:
            try:
                servo.enable_torque()  # Make sure torque is enabled
                servo.servo_mode()     # Ensure it's in servo mode
                servo.move(120)        # Move to 120 degrees
                print(f"Moved servo ID {servo.get_id()} to 120 degrees")
            except Exception as e:
                print(f"Error moving servo ID {servo.get_id()}: {str(e)}")
        
        print("\nMovement complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    move_all_servos_to_120()