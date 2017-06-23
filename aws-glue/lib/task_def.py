import boto3
from botocore.exceptions import ClientError

ecsc = boto3.client( "ecs" )

class ResourceKey():
    def __init__( self, **kwargs ):
        self.project  = kwargs["project"]
        self.variant  = kwargs["variant"]
        self.zone     = kwargs["zone"]

    def __str__(self):
        return "-".join( [ self.project, self.zone, self.variant ] )

    def task_def_name(self):
        return "-".join( [ "taskd", self.project, self.zone, self.variant ] )

    def service_name( self ):
        return "-".join( [ "svc", self.project, self.zone, self.variant ] )

def register( resource_key, **kwargs ):
    container_defs = list()
    for key, container in kwargs["containers"].items():
        ports = container.get( "ports", list() )
        ports = [ dict( hostPort = 0, containerPort = p, protocol = "tcp" ) for p in ports ]
        soft, hard = container["memory"]

        container_defs.append( dict(
            name              = key,
            portMappings      = ports,
            image             = kwargs[ "image" ],
            command           = container[ "main" ],
            environment       = [{ "name" : "ZONE", "value" : resource_key.zone }],
            memoryReservation = soft,
            memory            = hard,
            logConfiguration  = dict(
                logDriver = "awslogs",
                options   = {
                    "awslogs-group"         : kwargs["log_group"],
                    "awslogs-region"        : kwargs["region"],
                    "awslogs-stream-prefix" : resource_key.variant
                }
            )
        ) )

        ecsc.register_task_definition(
            family               = resource_key.task_def_name(),
            taskRoleArn          = kwargs["role"],
            containerDefinitions = container_defs
        )

def list_arns( **kwargs ):

    boto_kwargs = dict(
        familyPrefix = kwargs["family"],
        status       = kwargs.get("status", "ACTIVE" )
    )

    while True:
        resp = ecsc.list_task_definitions( ** boto_kwargs )
        for arn in resp["taskDefinitionArns"]:
            yield arn
        if "nextToken" not in resp:
            return
        boto_kwargs["nextToken"] = resp["nextToken"]

def list_families( **kwargs ):

    boto_kwargs = dict(
        familyPrefix = kwargs["prefix"],
        status       = kwargs.get( "status", "ACTIVE" )
    )

    while True:
        resp = ecsc.list_task_definition_families( ** boto_kwargs )
        for family in resp["families"]:
            yield family
        if "nextToken" not in resp:
            return
        boto_kwargs["nextToken"] = resp["nextToken"]

def try_update_service( resource_key, **kwargs ):
    try:
        ecsc.update_service(
            cluster        = kwargs["cluster"],
            service        = resource_key.service_name(),
            taskDefinition = resource_key.task_def_name()
        )
        return True
    except ClientError as e:
        print(e)
        return False
