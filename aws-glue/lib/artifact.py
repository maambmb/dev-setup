import boto3, tempfile, os, zipfile
from botocore.client import Config

s3c = boto3.client( "s3", config = Config(signature_version = "s3v4"))

def get_data( event ):

    job_data = event["CodePipeline.job"]["data"]
    artifact = job_data["inputArtifacts"][0]
    s3_info  = artifact["location"]["s3Location"]

    temp     = tempfile.gettempdir()
    zip_src  = os.path.join( temp, "input.zip" )

    bytes = s3c.get_object(
        Bucket = s3_info["bucketName"],
        Key    = s3_info["objectKey"]
    )["Body"].read()

    with open( zip_src, "wb" ) as zipf:
        zipf.write( bytes )

    return zipfile.ZipFile( zip_src, "r" )
