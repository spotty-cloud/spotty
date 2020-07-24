# FAQ

## How does Spotty choose the AWS Availability Zone where to run the instance?

1. If the AZ is specified in the configuration file, this AZ will be used to run the instance.
2. If the instance already has some EBS volumes created, Spotty will pick up the volumes' AZ.
3. Otherwise Spotty will let AWS choose an AZ. Automatically chosen AZ might not have the 
lowest Spot price, but in practice, it usually does.

Spotty will raise an error if the AZ in the configuration file doesn't match AZs of the volumes 
or AZs of the volumes are different.


## Why an instance is launching too long?

Most likely the instance cannot be launched because you're trying to launch a Spot instance
and it cannot be fulfilled. You can try to change the region or availability zone, choose another
type of the instance, or run an On-demand Instance by removing the `spotInstance` parameter or setting it to `false`.


## The instance is failed to start. Where can I find the logs?

1. If the CloudFormation stack failed when it was launching the instance itself, then you need to log in to
your AWS Console and check CloudFormation logs there.

2. If the stack is failed after the instance is launched, then most likely the container is
failed to start because of the startup commands. In this case, Spotty usually automatically downloads necessary 
logs to your local machine and shows where to find them. If that didn't happen, you can connect to the 
host OS using the following command:

    ```bash
    spotty sh -H
    ```
    
    Then you can check the `cfn-init` logs to find out why the container is failed:
    ```bash
    sudo tail /var/log/cfn-init-cmd.log
    ```

## How to ssh to a Spotty instance from a different machine?

When you start an instance, Spotty creates an EC2 Key Pair and downloads a private key to the 
`~/.spotty/keys/aws` directory. If you want to have access to the instance from a different machine using 
the `spotty sh` or the `spotty run` commands, you need to copy the private key to that machine to the same directory.

__Note:__ if you already have an EC2 Key Pair created for the project and the private key was 
saved on the machine A (where from an instance was launched the first time) and then you're running
an instance for the same project from the machine B that doesn't have a private key in the `~/.spotty/keys/aws` 
directory, then the EC2 Key Pair will be recreated and the machine A will not be able to connect to instances 
because its private key doesn't match the EC2 Key Pair anymore.
