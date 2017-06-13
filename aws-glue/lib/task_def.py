import boto3

ecsc = boto3.client( "ecs" )

def resource_key( ** kwargs ):
    return "-".join( [ kwargs["project"], kwargs["variant"], kwargs["zone"] ] )

def register( **kwargs ):
    taskd = "taskd-{0}".format( kwargs["resource_key"] )
    container_defs = list()
    for key, container in kwargs["containers"].items():

        ports = container.get( "ports", list() )
        ports = [ dict( hostPort = h, containerPort = c, protocol = "tcp" ) for [ c, h ] in ports ]

        container_defs.append( dict(
            name             = key,
            portMappings     = ports,
            image            = kwargs[ "image" ],
            command          = container[ "main" ],
            environment      = [ dict( name = "ZONE", value = kwargs["zone"] ) ],
            memory           = container[ "memory" ],
            logConfiguration = dict(
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

    kwargs = dict(
        familyPrefix = kwargs["family"],
        status       = kwargs.get("status", "ACTIVE" )
    )

    while True:
        resp = ecsc.list_task_definitions( ** kwargs )
        for arn in resp["taskDefinitionArns"]:
            yield arn
        if "nextToken" not in resp:
            return
        kwargs["nextToken"] = resp["nextToken"]

def list_families( **kwargs ):

    kwargs = dict(
        familyPrefix = kwargs["prefix"],
        status       = kwargs.get( "status", "ACTIVE" )
    )

    while True:
        resp = ecsc.list_task_definition_families( ** kwargs )
        for family in resp["families"]:
            yield family
        if "nextToken" not in resp:
            return
        kwargs["nextToken"] = resp["nextToken"]