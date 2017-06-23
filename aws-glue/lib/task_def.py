import boto3

ecsc = boto3.client( "ecs" )

def resource_key( ** kwargs ):
    return "-".join( [ kwargs["project"], kwargs["task_def"], kwargs["zone"] ] )

def register( **kwargs ):
    taskd = "taskd-{0}".format( kwargs["resource_key"] )
    container_defs = list()
    for key, container in kwargs["containers"].items():

        ports = container.get( "ports", list() )
        ports = [ dict( hostPort = 0, containerPort = p, protocol = "tcp" ) for p in ports ]
        soft, hard = container["memory"]

        env = [
            { "name" : "ZONE", "value" : kwargs["zone"] },
        ]

        container_defs.append( dict(
            name              = key,
            portMappings      = ports,
            image             = kwargs[ "image" ],
            command           = container[ "main" ],
            environment       = env,
            memoryReservation = soft,
            memory            = hard,
            logConfiguration  = dict(
                logDriver = "awslogs",
                options   = {
                    "awslogs-group"         : kwargs["log_group"],
                    "awslogs-region"        : kwargs["region"],
                    "awslogs-stream-prefix" : taskd
                }
            )
        ) )

        ecsc.register_task_definition(
            family               = taskd,
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
