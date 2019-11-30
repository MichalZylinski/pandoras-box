from google.cloud import spanner
from flask import Flask
from flask import render_template
from app.latencies import LatencyMetrics
import json
import os

app = Flask(__name__)
lm = LatencyMetrics(os.getenv("CONFIG_INSTANCE"))

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', instances=lm.available_instances)

@app.route('/metrics/<instance_id>')
def metrics(instance_id):
    lm.run_metrics(instance_id)
    return json.dumps(lm.latest_metrics)

@app.route('/updateInstance/<instance_id>')
def updateInstance(instance_id):
    updated_instance=lm.set_current_instance(instance_id)
    return json.dumps(updated_instance)


