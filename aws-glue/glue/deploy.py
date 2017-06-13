import boto3, json, traceback
from lib import artifact, task_def, service

iamc = boto3.client( "iam" )
ecrc = boto3.client( "ecr" )
ecsc = boto3.client( "ecs" )
cpc  = boto3.client( "codepipeline" )

def deploy( event, ctx ):
    try:
        job_id     = event["CodePipeline.job"]["id"]
        job_data   = event["CodePipeline.job"]["data"]
        zone       = job_data["actionConfiguration"]["configuration"]["UserParameters"]

        # UNPACK ARTIFACT DATA
        with artifact.get_data( event ) as zipf:
            tgt_image = zipf.read( "tgt_image" ).decode("utf-8").strip()
            purpose   = json.loads( zipf.read( "purpose.json" ).decode( "utf-8" ) )
            common    = json.loads( zipf.read( "common.json" ).decode( "utf-8" ) )
            site      = json.loads( zipf.read( "site.json" ).decode( "utf-8" ) )[ zone ]

        role = iamc.get_role( RoleName = common["taskRole"] )["Role"]["Arn"]
        for variant, cfg in purpose.items():

            resource_key = task_def.resource_key(
                project = common["project"],
                variant = variant,
                zone    = zone
            )

            # REGISTER TASK DEF
            print( "registering task definition: {0}".format( resource_key ) )
            task_def.register(
                zone         = zone,
                image        = tgt_image,
                role         = role,
                variant      = variant,
                resource_key = resource_key,
                region       = common["region"],
                log_group    = site["logGroup"],
                containers   = cfg["containers"]
            )

            # UPDATE SERVICE
            if cfg.get("service", False ):
                print( "attempting to update service: {0}".format( resource_key ) )
                service.try_update_service(
                    cluster      = site["cluster"],
                    resource_key = resource_key
                )

        cpc.put_job_success_result( jobId = job_id )

    except Exception as e:
        traceback.print_exc()
        cpc.put_job_failure_result(
            failureDetails = dict( type = "JobFailed", message = str(e) ),
            jobId          = job_id
        )
