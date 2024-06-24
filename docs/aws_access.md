# AWS S3 access

You do not need AWS credentials to download public files. 

To download private files or to upload files to S3, you will need an admin to create a user for you.
After you have received your credentials, you can configure your access in two ways:

## Option 1: configuration via command line
Use `awscli` to configure your AWS access.
```shell
pip install awscli
aws configure
```
(use region `us-east-1`, output-format `json`)

## Option 2: configuration via file
You can also create the configuration files yourself.

Create your credentials file at `~/.aws/credentials`:
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

To configure region and output format, create a config file at `~/.aws/config`:
```
[default]
region = us-east-1
output-format = json
```


# For admins: give access rights to new user
1. log in to the AWS browser console
2. [navigate to IAM, create new user](https://us-east-1.console.aws.amazon.com/iamv2/home?region=eu-central-1#/users/create) (in `us-east-1`)
3. for the username, use `<firstname>.<lastname>`, click next
4. add the user to the `Brain-Score_write` group if you want them to be able to upload new datasets/weights. They should only be able to upload, but not delete
5. click next, click create user
6. in the newly created user, go to `Security credentials`
7. click `Create access key` (use case CLI), click next
8. leave the tag blank, click `Create access key`
9. download the access key, send it to the user, along with a link to this file: https://github.com/brain-score/brainio/blob/main/docs/aws_access.md#aws-s3-access
