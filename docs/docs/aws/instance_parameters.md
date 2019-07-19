---
layout: default
title: Instance Parameters
parent: AWS Provider
nav_order: 1
permalink: /docs/aws-provider/instance-parameters/
---

# AWS Instance Parameters

- __`region`__ - AWS region where to run an instance (you can use command `spotty aws spot-prices` to find the 
cheapest region).

- __`availabilityZone`__ _(optional)_ - AWS availability zone where to run an instance. If a zone is not specified, it 
will be chosen automatically.

- __`subnetId`__ _(optional)_ - AWS subnet ID. If this parameter is set, the "availabilityZone" parameter should be 
set as well. If it's not specified, a default subnet will be used.

- __`instanceType`__ - a type of the instance to run. You can find more information about 
types of GPU instances here: 
[Recommended GPU Instances](https://docs.aws.amazon.com/dlami/latest/devguide/gpu.html){:target="_blank"}.

- __`onDemandInstance`__ _(optional)_ - run On-demand instance instead of a Spot instance. Available values: "true", 
"false" (default value is "false").

- __`amiName`__ _(optional)_ - a name of the AMI with NVIDIA Docker (default value is "SpottyAMI"). Use the 
`spotty aws create-ami` command to create it. This AMI will be used to run your application inside the Docker container.

- __`amiId`__ _(optional)_ - ID of the AMI with NVIDIA Docker. This parameter can be used to run an instance using a 
shared Spotty AMI.

- __`maxPrice`__ _(optional)_ - the maximum price per hour that you are willing to pay for a Spot Instance. By default, 
it's the On-demand price for the chosen instance type. Read more here: 
[Spot Instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html){:target="_blank"}.

- __`rootVolumeSize`__ _(optional)_ - size of the root volume in GB. The root volume will be destroyed once 
the instance is terminated. Use attached volumes to store the data you need to keep (see "volumes" parameter below).

- __`dockerDataRoot`__ _(optional)_ - directory where Docker will store all downloaded and built images. 
Read more: [How to cache a Docker image](/spotty/docs/faq/#how-to-cache-a-docker-image).

- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ - a name of the volume. This name should match one of the container's `volumeMounts` to have this 
    volume attached to the container's filesystem.

    - __`parameters`__ _(optional)_ - parameters of the volume:
        - __`size`__ _(optional)_ - size of the volume in GB. Size of the volume cannot be less than the size of 
        the existing snapshot but can be increased.

        - __`deletionPolicy`__ _(optional)_ - what to do with the volume once the instance is terminated using the 
        `spotty stop` command. Possible values include: "__create_snapshot__" _(value by default)_, "__update_snapshot__", 
        "__retain__" and  "__delete__". Read more: [Volumes and Deletion Policies](/spotty/docs/aws-provider/volumes-and-deletion-policies/).

        - __`volumeName`__ _(optional)_ - name of the EBS volume. The default name is 
        "{project_name}-{instance_name}-{volume_name}".

        - __`mountDir`__ _(optional)_ - directory where the volume will be mounted on the instance. The default 
        directory is "/mnt/{ebs_volume_name}".

- __`localSshPort`__ _(optional)_ - if the local SSH port is specified, the commands `spotty ssh`, `spotty run` 
and `spotty sync` will do SSH connections to the instance using the IP address __127.0.0.1__ and the specified port. 
It can be useful in case when the instance doesn't have a public IP address and SSH access is provided through a 
tunnel to a local port.

- __`managedPolicyArns`__ _(optional)_ - a list of Amazon Resource Names (ARNs) of the IAM managed policies that 
you want to attach to the instance role. Read more about Managed Policies 
[here](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html).

- __`commands`__ _(optional)_ - commands that should be run on the host OS before a container is started. 
For example, you could login to Amazon ECR to pull a Docker image from there 
([Deep Learning Containers Images](https://docs.aws.amazon.com/dlami/latest/devguide/deep-learning-containers-images.html)):
    ```yaml
    commands: |
      $(aws ecr get-login --no-include-email --region us-east-2 --registry-ids 763104351884)
    ```
