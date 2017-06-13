from lib import task_def, image
import boto3

ecsc = boto3.client( "ecs" )

def clean( cfg, ctx ):

    tags_to_keep   = set()
    tags_to_delete = set()

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

        # GRAB IMAGES FOR REMAINING ACTIVE TASK DEFS
        for tdef in tdefs:
            if "_marked" not in tdef:
                for img in tdef["images"]:
                    tags_to_keep.add( image.parse_tag( img ) )

    # FIND COMPLEMENT SET OF IMAGES AND DELETE
    tags_to_delete = set( x for x in image.get_tags( ** cfg ) if x not in tags_to_keep )
    if len(tags_to_delete) > 0:
        print( "deleting orphaned images" )
        image.delete_tags( ** cfg, tags = tags_to_delete )
