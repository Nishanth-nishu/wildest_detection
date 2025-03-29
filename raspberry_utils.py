import os
import time
import psutil
import logging
from typing import Tuple, Optional
from config import DetectionConfig

class RaspberryPiMonitor:
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def get_cpu_temperature(self) -> float:
        """Get CPU temperature in Celsius."""
        try:
            temp = os.popen("vcgencmd measure_temp").readline()
            return float(temp.replace("temp=", "").replace("'C", ""))
        except:
            return 0.0
            
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        return psutil.cpu_percent()
        
    def get_memory_usage(self) -> Tuple[float, float]:
        """Get memory usage in GB (used, total)."""
        memory = psutil.virtual_memory()
        return memory.used / (1024**3), memory.total / (1024**3)
        
    def check_system_status(self) -> bool:
        """Check if system is running within safe parameters."""
        if not self.config.enable_temp_monitoring:
            return True
            
        temp = self.get_cpu_temperature()
        if temp > self.config.temp_threshold:
            self.logger.warning(f"CPU temperature too high: {temp}°C")
            return False
            
        return True
        
    def optimize_for_power(self):
        """Apply power-saving optimizations."""
        if not self.config.power_save_mode:
            return
            
        # Reduce CPU frequency
        os.system("echo powersave | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        
        # Disable HDMI if no display is connected
        os.system("tvservice -o")
        
    def restore_normal_power(self):
        """Restore normal power settings."""
        if not self.config.power_save_mode:
            return
            
        # Restore CPU frequency
        os.system("echo ondemand | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        
        # Restore HDMI
        os.system("tvservice -p")
        
    def get_system_info(self) -> dict:
        """Get comprehensive system information."""
        return {
            "temperature": self.get_cpu_temperature(),
            "cpu_usage": self.get_cpu_usage(),
            "memory_used": self.get_memory_usage()[0],
            "memory_total": self.get_memory_usage()[1],
            "timestamp": time.time()
        } 