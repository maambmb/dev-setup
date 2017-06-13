import boto3
from botocore.exceptions import ClientError

ecsc = boto3.client( "ecs" )

def try_update_service( **kwargs ):
    try:
        ecsc.update_service(
            cluster        = kwargs["cluster"],
            service        = "svc-{0}".format( kwargs["resource_key"] ),
            taskDefinition = "taskd-{0}".format( kwargs["resource_key"] ),
        )
        return True
    except ClientError as e:
        print(e)
        return False
