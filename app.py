import psutil
import time 
from flask import Flask,render_template,jsonify
import platform 
import datetime

app = Flask(__name__) # setting up the app name

@app.route("/")  # / represents the home route

def index(): # renders the main dashboard with the initial metrics

    cpu_usage = psutil.cpu_percent(interval=1)  # stores the CPU usage
    memory_usage = psutil.virtual_memory().percent  # stores the memory usage percentage
    info=None
    if cpu_usage > 80 or memory_usage > 80:
        info ="High CPU or memory usage detected!"

    return render_template("index.html", cpu_metric=cpu_usage, mem_metric=memory_usage,message =info  )# renders the index.html file

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=5000)


#returns a log file everytime this script is made to run

@app.route("/system_data")

def system_data():

    """API endpoint to fetch system metrics for AJAX updates."""
    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()

    # Get disk usage for root partition
    disk = psutil.disk_usage('/')

    # Get network I/O stats
    network = psutil.net_io_counters()

    # Get top processes by CPU usage
    processes = []
    for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']),
                       key=lambda p: p.info['cpu_percent'] or 0,
                       reverse=True)[:5]:
        try:
            # Update CPU percent for accurate reading
            proc.cpu_percent()
            time.sleep(0.1)  # Small delay for more accurate CPU reading
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'][:20],  # Truncate long names
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.info['memory_percent'] or 0,
                'status': proc.info['status']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return jsonify({
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used': memory.used // (1024 * 1024),  # MB
        'memory_total': memory.total // (1024 * 1024),  # MB
        'disk_percent': disk.percent,
        'disk_used': disk.used // (1024 * 1024 * 1024),  # GB
        'disk_total': disk.total // (1024 * 1024 * 1024),  # GB
        'network_sent': network.bytes_sent,
        'network_recv': network.bytes_recv,
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



    #returns a log file everytime this script is made to run
