from google.cloud import spanner
from google.cloud.spanner_v1 import param_types
import timeit
import requests
import uuid
import time
import datetime
import os

#populating config database
config_instance_id='%sconfig' % os.getenv('TF_VAR_prefix')
config_database_id='config-database'
noReadings=5

target_instance_id=''
target_database_id=''
staleness=0
noReadings=0

client = spanner.Client()
config_instance = client.instance(config_instance_id)
config_database = config_instance.database(config_database_id)

available_instances = [instance.display_name for instance in client.list_instances() if instance.display_name != config_instance_id]

customer_database = 'testdb'
customer_table = 'customers'
sample_size = 3
staleness = 0
is_active = False
max_customers = 1000 #maximum number of customers/rows in database


rows = []
for i, instance in enumerate(available_instances, start=1):
    rows.append((i,sample_size, customer_database, instance, staleness, is_active))
with config_database.batch() as batch:
    batch.insert(
        table = "instances",
        columns = ('id','sample_size','instance_database_id','instance_id','staleness','is_active'),
        values = rows
    )

#activate first instance

def activate_first_instance(transaction):
    transaction.execute_update("UPDATE instances SET is_active=TRUE WHERE id=1")

config_database.run_in_transaction(activate_first_instance)
    
class CustomerBatch:
    """
    CustomerBatch class yields unique customer data structures in batches.
    """
    def __init__(self, batch_size=1000):
        self.batch_size=batch_size
        self.current_id = 1

    def next_batch(self):
        customer_list = []
        date = str(datetime.date.today())
        for i in range(self.current_id,self.current_id+self.batch_size):
            customer_list.append((self.current_id, date, str(uuid.uuid4())[1:10]))
            self.current_id += 1
        return customer_list


for current_instance in available_instances:
    print("Populating instance: %s" % current_instance)
    cust = CustomerBatch()
    while cust.current_id <= max_customers:
        with client.instance(current_instance).database(customer_database).batch() as batch:
            batch.insert(
                table=customer_table,
                columns=('customer_id','created_date','customer_name'),
                values=cust.next_batch()
            )

