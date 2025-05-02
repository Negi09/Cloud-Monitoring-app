import psutil
import time
import platform
import datetime
import os
import json
from collections import deque
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Create data stores for historical data
# Store last 60 minutes of data (with timestamps)
cpu_history = deque(maxlen=360)  # 1 hour at 10s intervals
memory_history = deque(maxlen=360)
disk_history = deque(maxlen=360)
network_recv_history = deque(maxlen=360)
network_sent_history = deque(maxlen=360)

@app.route("/")
def index():
    """Render the main dashboard page with initial metrics."""
    # Get initial CPU and memory usage to display on page load
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    
    # Check for high usage conditions
    info = None
    if cpu_usage > 80 or memory_usage > 80:
        info = "High CPU or memory usage detected!"
        
    return render_template(
        "index.html", 
        cpu_metric=cpu_usage, 
        mem_metric=memory_usage,
        message=info
    )

@app.route("/system_data")
def system_data():
    """API endpoint to fetch system metrics for AJAX updates."""
    # Get current timestamp
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    
    # Get disk usage for root partition
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Get network I/O stats
    network = psutil.net_io_counters()
    
    # Store historical data
    cpu_history.append((now.timestamp(), cpu_percent))
    memory_history.append((now.timestamp(), memory.percent))
    disk_history.append((now.timestamp(), disk_percent))
    network_recv_history.append((now.timestamp(), network.bytes_recv))
    network_sent_history.append((now.timestamp(), network.bytes_sent))
    
    # Get top processes by CPU usage
    processes = []
    try:
        # First collect all processes
        all_processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']))
        
        # Pre-compute CPU percentages
        for proc in all_processes:
            proc.cpu_percent()
        
        # Small delay for more accurate CPU readings
        time.sleep(0.1)
        
        # Sort by CPU percentage and get top 5
        for proc in sorted(all_processes, key=lambda p: p.cpu_percent(), reverse=True)[:5]:
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'][:20],  # Truncate long names
                    'cpu_percent': proc.cpu_percent(),
                    'memory_percent': proc.info['memory_percent'] or 0,
                    'status': proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"Error collecting process information: {e}")
    
    # Calculate network speeds (KB/s)
    network_speed = {'download': 0, 'upload': 0}
    if len(network_recv_history) >= 2:
        last_time, last_recv = network_recv_history[-2]
        current_time, current_recv = network_recv_history[-1]
        time_diff = current_time - last_time
        if time_diff > 0:
            network_speed['download'] = (current_recv - last_recv) / time_diff / 1024
        
        last_time, last_sent = network_sent_history[-2]
        current_time, current_sent = network_sent_history[-1]
        if time_diff > 0:
            network_speed['upload'] = (current_sent - last_sent) / time_diff / 1024
    
    return jsonify({
        'timestamp': timestamp,
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used': memory.used // (1024 * 1024),  # MB
        'memory_total': memory.total // (1024 * 1024),  # MB
        'disk_percent': disk_percent,
        'disk_used': disk.used // (1024 * 1024 * 1024),  # GB
        'disk_total': disk.total // (1024 * 1024 * 1024),  # GB
        'network_sent': network.bytes_sent,
        'network_recv': network.bytes_recv,
        'network_speed': network_speed,
        'processes': processes,
        'system_info': {
            'system': platform.system(),
            'release': platform.release(),
            'hostname': platform.node(),
            'uptime': round((time.time() - psutil.boot_time()) / 3600, 2)  # Hours
        }
    })

@app.route("/system_info")
def system_info():
    """Return detailed system information."""
    # CPU information
    cpu_freq = psutil.cpu_freq()
    cpu_info = {
        'physical_cores': psutil.cpu_count(logical=False),
        'total_cores': psutil.cpu_count(logical=True),
        'max_frequency': cpu_freq.max if cpu_freq else "N/A",
        'current_frequency': cpu_freq.current if cpu_freq else "N/A",
        'cpu_usage_per_core': [percentage for percentage in psutil.cpu_percent(percpu=True)]
    }
    
    # Memory information
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    memory_info = {
        'total': memory.total // (1024 * 1024),  # MB
        'available': memory.available // (1024 * 1024),  # MB
        'used': memory.used // (1024 * 1024),  # MB
        'swap_total': swap.total // (1024 * 1024),  # MB
        'swap_used': swap.used // (1024 * 1024)  # MB
    }
    
    # Disk information
    partitions = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'filesystem': partition.fstype,
                'total': usage.total // (1024 * 1024 * 1024),  # GB
                'used': usage.used // (1024 * 1024 * 1024),  # GB
                'percent': usage.percent
            })
        except (PermissionError, FileNotFoundError):
            # Some disk partitions aren't readable
            continue
    
    # Network interfaces
    network_interfaces = []
    for interface_name, interface_addresses in psutil.net_if_addrs().items():
        mac = ipv4 = ipv6 = 'N/A'
        for address in interface_addresses:
            if address.family == psutil.AF_LINK:
                mac = address.address
            elif address.family == 2:  # IPv4
                ipv4 = address.address
            elif address.family == 23:  # IPv6
                ipv6 = address.address
                
        # Get network stats if available
        io_counters = psutil.net_io_counters(pernic=True).get(interface_name)
        bytes_sent = bytes_recv = packets_sent = packets_recv = 0
        if io_counters:
            bytes_sent = io_counters.bytes_sent
            bytes_recv = io_counters.bytes_recv
            packets_sent = io_counters.packets_sent
            packets_recv = io_counters.packets_recv
                
        network_interfaces.append({
            'interface': interface_name,
            'mac': mac,
            'ipv4': ipv4,
            'ipv6': ipv6,
            'bytes_sent': bytes_sent,
            'bytes_recv': bytes_recv,
            'packets_sent': packets_sent,
            'packets_recv': packets_recv
        })
        
    return jsonify({
        'cpu': cpu_info,
        'memory': memory_info,
        'disk': partitions,
        'network': network_interfaces,
        'system': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'uptime': round((time.time() - psutil.boot_time()) / 3600, 2)  # Hours
        }
    })

@app.route('/history_data')
def history_data():
    """Return historical data for charts with time range support."""
    time_range = request.args.get('range', '5m')  # Default to 5 minutes
    
    # Calculate the cutoff time based on requested range
    now = datetime.datetime.now().timestamp()
    if time_range == '5m':
        cutoff = now - 5 * 60  # 5 minutes
    elif time_range == '15m':
        cutoff = now - 15 * 60  # 15 minutes
    elif time_range == '1h':
        cutoff = now - 60 * 60  # 1 hour
    else:
        cutoff = now - 5 * 60  # Default to 5 minutes
    
    # Filter data based on cutoff time
    cpu_data = [(t, v) for t, v in cpu_history if t >= cutoff]
    memory_data = [(t, v) for t, v in memory_history if t >= cutoff]
    disk_data = [(t, v) for t, v in disk_history if t >= cutoff]
    
    # Format timestamps for display
    formatted_cpu = [{"x": datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S'), "y": v} for t, v in cpu_data]
    formatted_memory = [{"x": datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S'), "y": v} for t, v in memory_data]
    formatted_disk = [{"x": datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S'), "y": v} for t, v in disk_data]
    
    # Calculate network speed history
    network_download = []
    network_upload = []
    
    if len(network_recv_history) >= 2:
        recv_data = [d for d in network_recv_history if d[0] >= cutoff]
        sent_data = [d for d in network_sent_history if d[0] >= cutoff]
        
        for i in range(1, len(recv_data)):
            prev_time, prev_recv = recv_data[i-1]
            curr_time, curr_recv = recv_data[i]
            time_diff = curr_time - prev_time
            
            if time_diff > 0:
                download_speed = (curr_recv - prev_recv) / time_diff / 1024  # KB/s
                formatted_time = datetime.datetime.fromtimestamp(curr_time).strftime('%H:%M:%S')
                network_download.append({"x": formatted_time, "y": download_speed})
        
        for i in range(1, len(sent_data)):
            prev_time, prev_sent = sent_data[i-1]
            curr_time, curr_sent = sent_data[i]
            time_diff = curr_time - prev_time
            
            if time_diff > 0:
                upload_speed = (curr_sent - prev_sent) / time_diff / 1024  # KB/s
                formatted_time = datetime.datetime.fromtimestamp(curr_time).strftime('%H:%M:%S')
                network_upload.append({"x": formatted_time, "y": upload_speed})
    
    return jsonify({
        'cpu': formatted_cpu,
        'memory': formatted_memory,
        'disk': formatted_disk,
        'network': {
            'download': network_download,
            'upload': network_upload
        },
        'range': time_range
    })

if __name__ == '__main__':
    # Pre-populate some initial dummy data for charts
    now = datetime.datetime.now().timestamp()
    for i in range(10):
        back_time = now - (10-i) * 10
        cpu_history.append((back_time, 0))
        memory_history.append((back_time, 0))
        disk_history.append((back_time, 0))
        network_recv_history.append((back_time, 0))  
        network_sent_history.append((back_time, 0))
    
    print("Starting System Monitoring Dashboard...")
    print("Open your browser and navigate to http://localhost:5000")
    app.run(debug=True, host='0.0.0.0')   #returns a log file everytime this script is made to run
