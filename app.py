import psutil
from flask import Flask,render_template

app = Flask(__name__) # setting up the app name

@app.route("/")  # / represents the home route
def index():
    cpu_usage = psutil.cpu_percent(interval=1)  # stores the CPU usage
    memory_usage = psutil.virtual_memory().percent  # stores the memory usage percentage
    info=None
    if cpu_usage > 80 or memory_usage > 80:
        info ="High CPU or memory usage detected!"

    return render_template("index.html", cpu_metric=cpu_usage, mem_metric=memory_usage,message =info  )# renders the index.html file

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=5000)


#returns a log file everytime this script is made to run 
