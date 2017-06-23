from lib import task_def, image
import boto3, sys

ecsc = boto3.client( "ecs" )

def clean( cfg, ctx ):

    # FOR EACH TASK FAMILY IN A PROJECT
    print( "grabbing all task def families for project" )
    for family in task_def.list_families( status = "ACTIVE", prefix = "taskd-{0}".format( cfg["project"] ) ):

        # GRAB ALL TASK DEFINITIONS THAT ARE ACTIVE
        tdefs = list()

        print( "grabbing all task def revision for family: {0}".format( family ) )
        for arn in task_def.list_arns( status = "ACTIVE", family = family ):

            tdef  = ecsc.describe_task_definition( taskDefinition = arn )["taskDefinition"]
            tdefs.append( dict(
                arn      = arn,
                revision = tdef["revision"],
                family   = tdef["family"],
                images   = [ x["image"] for x in tdef["containerDefinitions"] ]
            ) )

        # SORT BY REVISION AND DELETE OLDEST
        tdefs.sort( key = lambda x : x["revision"] )
        for tdef in tdefs[:-cfg["buffer"]]:
            tdef["_marked"] = True
            print( "deregistering revision: {0}".format( tdef["revision"] ) )
            ecsc.deregister_task_definition( taskDefinition = tdef["arn"] )

        # GRAB IMAGES FOR REMAINING ACTIVE TASK DEFS AND GET OLDEST TIMESTAMP
        cutoff_ts = sys.maxsize
        for tdef in tdefs:
            if "_marked" not in tdef:
                for img in tdef["images"]:
                    cutoff_ts = min( cutoff_ts, image.parse_tag( uri = img )[1] )

    # DELETE ALL IMAGES WITH OLDER TIMESTAMPS
    tags_to_delete = [ x for x in image.get_tags( ** cfg ) if image.parse_tag( tag = x )[1] < cutoff_ts ]
    if len(tags_to_delete) > 0:
        print( "deleting {0} orphaned images".format( len( tags_to_delete ) ) )
        image.delete_tags( ** cfg, tags = tags_to_delete )
