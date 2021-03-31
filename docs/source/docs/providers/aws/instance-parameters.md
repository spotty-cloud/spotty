# Instance Parameters

Instance parameters are part of the [configuration file], but for each provider they are different. 
Here you can find parameters for an AWS instance:

- __`containerName`__ _(optional)_ - a name of the container from the `containers` section.
Default value: `default`.

- __`region`__ - AWS region where to run an instance (you can use command `spotty aws spot-prices` to find the 
cheapest region).

- __`availabilityZone`__ _(optional)_ - AWS availability zone where to run an instance. If a zone is not specified, it 
will be chosen automatically.

- __`subnetId`__ _(optional)_ - AWS subnet ID. If this parameter is set, the "availabilityZone" parameter should be 
set as well. If it's not specified, a default subnet will be used.

- __`instanceType`__ - a type of the instance to run. You can find more information about 
types of GPU instances here: 
[Recommended GPU Instances](https://docs.aws.amazon.com/dlami/latest/devguide/gpu.html).

- __`spotInstance`__ _(optional)_ - if set to `true`, runs a Spot instance instead of an On-demand instance,

- __`amiName`__ _(optional)_ - a name of the AMI with NVIDIA Docker (default value is "SpottyAMI"). Use the 
`spotty aws create-ami` command to create it. This AMI will be used to run your application inside the Docker container.

- __`amiId`__ _(optional)_ - ID of the AMI with NVIDIA Docker. This parameter can be used to run an instance using a 
shared Spotty AMI.

- __`maxPrice`__ _(optional)_ - the maximum price per hour that you are willing to pay for a Spot Instance. By default, 
it's the On-demand price for the chosen instance type. Read more here: 
[Spot Instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html).

- __`rootVolumeSize`__ _(optional)_ - size of the root volume in GB. The root volume will be destroyed once 
the instance is terminated. Use attached volumes to store the data you need to keep (see "volumes" parameter below).

- __`dockerDataRoot`__ _(optional)_ - directory where Docker will store all downloaded and built images. 
Read more: [Caching Docker Image on an EBS Volume].

- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ - a name of the volume. This name should match one of the container's `volumeMounts` to have this 
    volume attached to the container's filesystem.

    - __`parameters`__ _(optional)_ - parameters of the volume:
        - __`type`__ _(optional)_ - the volume type. Supported types: "__gp2__", "__sc1__", "__st1__" 
        and "__standard__". The default value is "gp2". Read more here: 
        [Amazon EBS Volume Types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumeTypes.html).
    
        - __`size`__ _(optional)_ - size of the volume in GB. Size of the volume cannot be less than the size of 
        the existing snapshot but can be increased.

        - __`deletionPolicy`__ _(optional)_ - what to do with the volume once the instance is terminated using the 
        `spotty stop` command. Possible values include: "__Retain__" _(value by default)_, "__CreateSnapshot__", 
        "__UpdateSnapshot__" and  "__Delete__". Read more here: [EBS Volumes and Deletion Policies].

        - __`volumeName`__ _(optional)_ - name of the EBS volume. The default name is 
        "{project_name}-{instance_name}-{volume_name}".

        - __`mountDir`__ _(optional)_ - directory where the volume will be mounted on the instance. The default 
        directory is "/mnt/{ebs_volume_name}".

- __`ports`__ _(optional)_ - list of ports to open on the instance. For example:
    ```yaml
    ports: [6006, 8888]
    ```
    It will open ports 6006 for TensorBoard and 8888 for Jupyter Notebook. 

-__`inboundIp`__ _(optional)_ - an IP address or CIDR range to use as a whitelist for all ports provided
to the security group. The default is to not use a whitelist. 

- __`localSshPort`__ _(optional)_ - if this parameter is set, all the Spotty commands will create SSH connections 
with the instance using the IP address __127.0.0.1__ and the specified port. This can be useful in case when an 
instance doesn't have a public IP address and a jump-server is used for tunneling.

- __`managedPolicyArns`__ _(optional)_ - a list of Amazon Resource Names (ARNs) of the IAM managed policies that 
you want to attach to the instance role. Read more about Managed Policies 
[here](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html).

- __`instanceProfileArn`__ _(optional)_ - an Amazon Resource Name (ARN) of the IAM Instance Profile that you'd like
to attach to the instance. Read more about Instance Profiles
[here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html).

- __`commands`__ _(optional)_ - commands that should be run on the host OS before the container is started. 
For example, you could login to Amazon ECR to pull a Docker image from there 
([Deep Learning Containers Images](https://docs.aws.amazon.com/dlami/latest/devguide/deep-learning-containers-images.html)):
    ```yaml
    commands: |
      $(aws ecr get-login --no-include-email --region us-east-2 --registry-ids 763104351884)
    ```


[configuration file]: </docs/user-guide/configuration-file>
[Caching Docker Image on an EBS Volume]: </docs/providers/aws/caching-docker-image-on-an-ebs-volume>
[EBS Volumes and Deletion Policies]: </docs/providers/aws/ebs-volumes-and-deletion-policies>
