AWS Glue
=======

## Usage

```
python3 deploy
```

## Actions

Hoists the following functions/scripts to AWS Lambda:

  1. `deploy.py` - used after a CodeBuild pipeline stage to construct and update relevant task defs and services.
  2. `clean.py` - run at a regular interval to clean up unused ECR images and task definitions

