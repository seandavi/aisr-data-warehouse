"""A Google Cloud Python Pulumi program"""

from re import I
import pulumi
import pulumi_gcp as gcp

# Create a GCP resource (Storage Bucket)
bucket = gcp.storage.Bucket('uccc-aisr')

# healthcare api stuff
healthcare_dataset = gcp.healthcare.Dataset("uccc-aisr",
    location="us-central1",
    time_zone="UTC"
)

config = pulumi.Config('gcp')
project = config.require('project')

bigquery_dataset = gcp.bigquery.Dataset('uccc_aisr',
    dataset_id='uccc_aisr',
    location="US",
    delete_contents_on_destroy=True
)

bigquery_table = gcp.bigquery.Table("dicom",
    deletion_protection=False,
    dataset_id = bigquery_dataset.dataset_id,
    table_id='dicom'
)

output = pulumi.Output.all(bigquery_dataset.project,bigquery_dataset.dataset_id,bigquery_table.table_id)
print(output)
bqstreamconfig = gcp.healthcare.DicomStoreStreamConfigBigqueryDestinationArgs(
    table_uri = output.apply(lambda dat: f"bq://{dat[0]}.{dat[1]}.{dat[2]}")
)

streamconfig = [gcp.healthcare.DicomStoreStreamConfigArgs(
    bigquery_destination=bqstreamconfig
)]

pubsub_new_dicom = gcp.pubsub.Topic("new_dicom")

pubsub_new_dicom_sub = gcp.pubsub.Subscription('new_dicom_subscription',
    topic= pubsub_new_dicom
)

dicom_store = gcp.healthcare.DicomStore('uccc-aisr',
    dataset = healthcare_dataset,
    notification_config=gcp.healthcare.DicomStoreNotificationConfigArgs(pubsub_topic = pubsub_new_dicom)
#    stream_configs=streamconfig
)


# Export the DNS name of the bucket
pulumi.export('project',project)
pulumi.export('bucket_name', bucket.url)
pulumi.export('healthcare_dataset_name',healthcare_dataset.name)
pulumi.export('dicom_store_name',dicom_store.name)
pulumi.export("bq_dataset_name", bigquery_dataset.dataset_id)
pulumi.export("bq_table_name", bigquery_table.table_id)
pulumi.export("pubsub_topic", pubsub_new_dicom.name)

#config = pulumi.Config('google-native')
#project = config.require('project')





