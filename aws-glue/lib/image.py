import boto3

ecrc = boto3.client( "ecr" )

def get_tags( ** kwargs ):

    kwargs = dict(
        registryId     = str(kwargs["account_id"]),
        repositoryName = kwargs["repository_name"]
    )

    while True:
        resp = ecrc.list_images( **kwargs )
        for img in resp["imageIds"]:
            tag = img["imageTag"]
            if "project" not in kwargs or tag.split(".")[0] == kwargs["project"]:
                yield tag
        if "nextToken" not in resp:
            return
        kwargs["nextToken"] = resp["nextToken"]

def delete_tags( **kwargs ):
    ecrc.batch_delete_image(
        registryId     = str(kwargs["account_id"]),
        repositoryName = kwargs["repository_name"],
        imageIds       = [ { "imageTag" : x } for x in kwargs["tags"] ]
    )

def parse_tag( uri ):
    return uri.split("/")[1].split(":")[1]
