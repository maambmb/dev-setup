import boto3, json, traceback, os
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

        core_path   = os.path.join( "cfg", zone, "core.json" )
        tdef_prefix = os.path.join( "cfg", zone, "taskdef" )

        with artifact.get_data( event ) as zipf:
            img  = zipf.read("tgt_image").decode("utf-8")
            core = json.loads( zipf.read( core_path ).decode( "utf-8" ) )
            role = iamc.get_role( RoleName = core["taskRole"] )["Role"]["Arn"]

            for path in zipf.namelist():

                if not path.startswith( tdef_prefix ):
                    continue

                cfg = json.loads( zipf.read( path ).decode( "utf-8" ) )

                tdef = os.path.splitext( os.path.basename( path ) )[0]
                resource_key = task_def.resource_key(
                    project  = core["project"],
                    task_def = tdef,
                    zone     = zone
                )

                # REGISTER TASK DEF
                print( "registering task definition: {0}".format( resource_key ) )
                task_def.register(
                    zone         = zone,
                    image        = img,
                    role         = role,
                    task_def     = tdef,
                    resource_key = resource_key,
                    region       = core["region"],
                    log_group    = core["logGroup"],
                    containers   = cfg["containers"]
                )

                # UPDATE SERVICE
                if cfg.get("service", False ):
                    print( "attempting to update service: {0}".format( resource_key ) )
                    service.try_update_service(
                        cluster      = core["cluster"],
                        resource_key = resource_key
                    )

        cpc.put_job_success_result( jobId = job_id )

    except Exception as e:
        traceback.print_exc()
        cpc.put_job_failure_result(
            failureDetails = dict( type = "JobFailed", message = str(e) ),
            jobId          = job_id
        )
