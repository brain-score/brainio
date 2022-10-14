# AWS S3 access

You do not need AWS access to download many files as long as they are public.

To upload files to S3, you will need an admin to create a user for you.
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
