"""A Google Cloud Python Pulumi program"""

from re import I
import pulumi
import pulumi_gcp as gcp
import pulumi_docker as docker
import os

# Create a GCP resource (Storage Bucket)
bucket = gcp.storage.Bucket('uccc-aisr')

# bigquery stuff
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

# healthcare api stuff
healthcare_dataset = gcp.healthcare.Dataset("uccc-aisr",
    location="us-central1",
    time_zone="UTC"
)

output = pulumi.Output.all(bigquery_dataset.project,bigquery_dataset.dataset_id,bigquery_table.table_id)
bqstreamconfig = gcp.healthcare.DicomStoreStreamConfigBigqueryDestinationArgs(
    table_uri = output.apply(lambda dat: f"bq://{dat[0]}.{dat[1]}.{dat[2]}")
)

streamconfig = [gcp.healthcare.DicomStoreStreamConfigArgs(
    bigquery_destination=bqstreamconfig
)]

# dicom pubsub stuff 
#
# this generates a message ONLY WHEN
# DIRECTLY ADDING DICOM, not GCS import
pubsub_new_dicom = gcp.pubsub.Topic("new_dicom")

pubsub_new_dicom_sub = gcp.pubsub.Subscription('new_dicom_subscription',
    topic= pubsub_new_dicom
)

dicom_store = gcp.healthcare.DicomStore('uccc-aisr',
    dataset = healthcare_dataset,
    notification_config=gcp.healthcare.DicomStoreNotificationConfigArgs(pubsub_topic = pubsub_new_dicom)
#    stream_configs=streamconfig
)



#config = pulumi.Config('google-native')
#project = config.require('project')

enable_cloudrun = gcp.projects.Service("enable_cloud_run",
    service= "run.googleapis.com"
)

image_registry = gcp.container.Registry('image_registry')
registry_url = image_registry.id.apply(lambda _: gcp.container.get_registry_repository().repository_url)
image_name = registry_url.apply(lambda url: f'{url}/ohif-viewer')

image = docker.Image('ohif-viewer',
   image_name = image_name,
   build=docker.DockerBuild(context='.'),
   registry = None
)

ohif_viewer = gcp.cloudrun.Service("ohif-viewer",
    location="us-central1",
    template=gcp.cloudrun.ServiceTemplateArgs(
        spec=gcp.cloudrun.ServiceTemplateSpecArgs(
            containers=[gcp.cloudrun.ServiceTemplateSpecContainerArgs(
                image=image.base_image_name,
                envs=[
                    gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                        name="CLIENT_ID",
                        value=os.getenv("GOOGLE_CLIENT_ID"),
                    )
                ],
            )],
        ),
    ),
    traffics=[gcp.cloudrun.ServiceTrafficArgs(
        latest_revision=True,
        percent=100,
    )],
    metadata=gcp.cloudrun.ServiceMetadataArgs(
        annotations = {"run.googleapis.com/ingress":"all"}
    ),
    opts = pulumi.ResourceOptions(depends_on=[enable_cloudrun,image])
    )

binding = gcp.cloudrun.IamBinding("binding",
    location=ohif_viewer.location,
    project=ohif_viewer.project,
    service=ohif_viewer.name,
    role="roles/run.invoker",
    members=["allUsers"])

# Exports
pulumi.export('bucket_name', bucket.url)
pulumi.export('healthcare_dataset_name',healthcare_dataset.name)
pulumi.export('dicom_store_name',dicom_store.name)
pulumi.export("bq_dataset_name", bigquery_dataset.dataset_id)
pulumi.export("bq_table_name", bigquery_table.table_id)
pulumi.export("pubsub_topic", pubsub_new_dicom.name)
pulumi.export('cloudrun_ip',ohif_viewer.statuses[0].url)

