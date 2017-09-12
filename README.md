# ssha

ssha makes it easy to SSH into AWS EC2 instances.

Features:

* discovery of EC2 instances
* bastion/jump host support
* automatic user/key creation with SSM

ssha uses a project-specific `.ssha` file, so users (or customers less familiar with AWS) don't need to know the architecture. This file would generally live in a project's infrastructure repository, so that everyone can use the same configuration.

## Requirements

* Linux/Unix
* AWS CLI profiles
* AWS EC2 instances
* Python 2.7 or 3.x

## Installation

```shell
pip install ssha
```

## Usage

ssha looks in the current directory, or parent directories, for a `.ssha` file. Once you have ssha installed and your `.ssha` file there, just run `ssha`.

General usage:

```shell
ssha
```

Show the installed version:

```shell
ssha --version
```

Show the command line options:

```shell
ssha --help
```

## Settings file

The `.ssha` file is a flexible document that defines how a project can be accessed. The document format is [HCL](https://github.com/hashicorp/hcl). If you have used [Terraform](https://github.com/hashicorp/terraform) then it may be familiar.

See the [examples](examples/) directory for complete examples of `.ssha` files.

### `ssha {}`

The `ssha` block defines a project name, and the `configs` for the project.

```js
ssha {
  /*
  This currently does nothing, but may be used in the future.
  */
  name = "my-project"

  /*
  This defines the configs for the project. In this example,
  each config represents a different environment in the project.
  */
  configs = ["dev", "stage", "prod"]
}
```

### `aws {}`

The `aws` block defines the AWS profile or credentials used to access the AWS API. This is used to create a [boto3 session](http://boto3.readthedocs.io/en/latest/reference/core/session.html#boto3.session.Session) so it supports those parameters.

It is recommended that you define profiles in `~/.aws/config` as per the [AWS CLI documentation](http://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html) and only refer to profile names in the `.ssha` file.

```js
aws {
  profile_name = "my-project"
}
```

### `bastion {}`

Instances in a private subnet might require a "bastion" or "jump" host. If the `bastion` block is defined, ssha will use it to find a bastion host to use when SSHing into any non-bastion host.

The `bastion` and `discovery` blocks use the same configuration syntax. See the `discovery` documentation for more information.

### `discover {}`

The `discover` block controls which instances will be shown to the user.

The nested `ec2` block is used to filter results from an [ec2:DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html) API call.

The nested `ssm` block is used to filter results from an [ssm:DescribeInstanceInformation](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_DescribeInstanceInformation.html) API call.

```js
discover {
  /*
  Define EC2 filters for finding relevant instances.
  */
  ec2 {
    State {
      Name = "running"
    }

    Tags {
      /*
      ${config.name} is a variable that resolves to the
      name of the config that was selected by the user.
      */
      Environment = "${config.name}"
      Service     = "bastion"
    }
  }

  /*
  Define SSM filters for finding relevant instances.
  */
  ssm {
    PingStatus = "Online"
  }
}
```

### `display {}`

The `display` block controls how instances are displayed.

```js
display {
  /*
  Use these fields when displaying an instance.
  */
  fields = ["InstanceId", "Tags.Service"]

  /*
  Sort instances by these fields.
  */
  sort  = ["Tags.Service", "InstanceId"]
}
```

### `ssh {}`

ssha is not an SSH client; it instead figures out the right `ssh` command to run. The `ssh` block controls some of the options that will be passed to the `ssh` command.

```js
ssh {
  /*
  The default username can be overridden if necessary.
  If not defined, the default SSH user name is used.
  */
  username = "ec2-user"

  /*
  ${ssm.host_keys_file} is a variable that resolves to a temporary file that
  is generated from the SSM command output. For this to work, the SSM document
  command must print the server's SSH host keys to stdout. The host keys can be
  printed with `ssh-keyscan localhost`. Any other commands printing to stdout
  should be redirected to /dev/null so that the output contains the host keys
  and nothing else.
  */
  user_known_hosts_file = "${ssm.host_keys_file}"
}
```

Computed values:

* `ssh.identityfile_public` - This is the path of the first `.pub` file that matches a private identity file in the SSH config. The primary use case for this is to install it onto a server using the SSM command, allowing key based authentication.
* `ssh.username` - This defaults to the default user in the SSH config.

### `ssm {}`

The `ssm` block controls SSM behaviour. The use case for this is to run a command on the instance that creates a user and adds their SSH key. This allows for SSH access to EC2 instances that is restricted by IAM access; whoever has IAM access to the SSM document is allowed to give themselves SSH access to EC2 instances

This requires the EC2 instances to be using the SSM agent, and it requires an SSM document that handles user creation.

```js
ssm {
  document {
    name = "add-ssh-key"
  }

  parameters {
    username = ["${ssh.username}"]
    key      = ["$(cat '${ssh.identityfile_public}')"]
  }
}
```

Computed values:

* `ssm.host_keys_file` - This is the path of a temporary file that is is generated from the SSM command output. For this to work, the SSM document command must print the server's SSH host keys to stdout. The host keys can be printed with `ssh-keyscan localhost`. Any other commands printing to stdout should be redirected to /dev/null so that the output contains the host keys and nothing else.

### `config [name] {}`

Blocks can be updated per config.

```js
ssha {
  name = "my-project"
  configs = ["dev", "stage", "prod"]
}

/*
Configs use this AWS profile by default.
*/
aws {
  profile_name = "my-project-nonprod"
}

/*
The "prod" config uses a different AWS profile.
*/
config prod {
  aws {
    profile_name = "my-project-prod"
  }
}
```

### `iam group [name] ... {}`

Blocks can be updated per IAM user group.

The use case for this is to have certain users with SSH access restricted to a subset of EC2 instances.

```js
iam group developers {
  /*
  Use a different document with more restrictions.
  */
  ssm document {
    name = "add-ssh-key-developers"
  }

  /*
  Add an extra filter to only use bastion instances with this tag.
  */
  bastion ec2 Tags {
    "SSH:developers" = ""
  }

  /*
  Add an extra filter to only show instances with this tag.
  */
  discover ec2 Tags {
    "SSH:developers" = ""
  }
}
```

## Contributing

If you have an idea for a new feature, please submit an issue first to confirm whether a pull request would be accepted.

### Style guide

* PEP 8
* 120 character limit
