from google.cloud import spanner
import timeit
import subprocess
import random
import uuid
import time
import datetime
import os

config_instance_id=os.getenv("CONFIG_INSTANCE")
config_database_id='config-database'

zone = subprocess.Popen('curl -H Metadata-Flavor:Google -s http://metadata/computeMetadata/v1/instance/zone| cut -d/ -f4', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.readlines()[0][:-1]
vm_id = os.getenv('HOSTNAME')

client = spanner.Client()
instance = client.instance(config_instance_id)
database = instance.database(config_database_id)

max_customers = 1000

def get_current_instance():
    with database.snapshot(multi_use=True) as snapshot:
        results = snapshot.execute_sql(
            "SELECT instance_id, instance_database_id, staleness, sample_size FROM instances WHERE is_active=true"
        )
        return results.one()
        

def read_data(database, staleness, max_id=max_customers):
    "Reads random row from active database and returns operation latency in ms"
    start_time = timeit.default_timer()
    if staleness == 0:
        interval=None
    else:
        interval = datetime.timedelta(seconds=staleness)
    with database.snapshot(max_staleness=interval) as snapshot:
        QUERY = (
            'SELECT customer_id,customer_name FROM customers where customer_id=%s' % random.randint(1,max_id)
        )
        result = snapshot.execute_sql(QUERY)
    return timeit.default_timer() - start_time



def log_metrics(transaction,metric):
    "Writes metrics into latency table"

    transaction.insert(
        'latencyMetrics', columns=['reading_id','vm_id','latency', 'zone', 'insertedTimestamp','instanceName'],
        values=metric
    )


while True:
    #getting current configuration
    try:
        instance_id, database_id, staleness, sample_size = get_current_instance()
    except:
        print("ERROR:Cannot connect to credentials database")
    #running measurement    
    try:
        target_instance = client.instance(instance_id)
        target_database = target_instance.database(database_id)

        latency=[]

        for i in range(0,sample_size):
            timing = read_data(target_database, staleness)
            latency.append(timing)
        try:
            #saving latency metrics into Spanner table
            metric = []
            for l in latency:
                metric.append([str(uuid.uuid4()), vm_id, l, zone, spanner.COMMIT_TIMESTAMP, instance_id])

            database.run_in_transaction(log_metrics, metric)

            time.sleep(10)
        except:
            print("ERROR:Cannot connect to logging database")
    except:
        print("ERROR:Cannot connect to target database")


