from google.cloud import spanner
import os

class LatencyMetrics:
    def __init__(self, config_instance_id):
        self.client = spanner.Client()
        self.config_instance = self.client.instance(config_instance_id)
        self.config_database = self.config_instance.database("config-database")
        self.available_instances = self.get_available_instances()
        self.latest_metrics=[]

    def set_current_instance(self, instance_id):
        if instance_id not in self.available_instances:
            raise ValueError("Instance does not exist")
        def set_instance(transaction):
            transaction.execute_update("UPDATE instances SET is_active=false WHERE 1=1")
            transaction.execute_update("UPDATE instances SET is_active=true WHERE instance_id=@InstanceId",
            params={"InstanceId": instance_id},
            param_types={"InstanceId": spanner.param_types.STRING})

        self.config_database.run_in_transaction(set_instance)
        return instance_id

    def get_current_instance(self):
        "Returns current instance info in a form of (instance_id, database_id)"
        with self.config_database.snapshot() as snapshot:
            results = snapshot.execute_sql(
            'SELECT instance_id, instance_database_id FROM instances WHERE is_active=true')
        return results.one()
        
    def get_available_instances(self):
        "Returns list of available spannerhammer instances"
        with self.config_database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                "SELECT instance_id FROM instances ORDER by instance_id"
            )
        return [instance[0] for instance in results]

    def run_metrics(self, instance_id):
        rowlist=[]
        self.latest_metrics=[]
        with self.config_database.snapshot() as snapshot:
            QUERY = (
                "SELECT vm_id,zone,instanceName,avg(latency) FROM latencyMetrics "
                "WHERE insertedTimestamp >= TIMESTAMP_SUB(current_timestamp(),INTERVAL 60 SECOND) "
                "and instanceName='" + instance_id +"'"+
                " group by vm_id,zone,instanceName")
            result = snapshot.execute_sql(QUERY)
            for row in result:
                self.latest_metrics.append({'vm_id':str(row[0])[:-1],'zone':str(row[1]).strip(),'instanceName':str(row[2]),'latency':row[3]})

