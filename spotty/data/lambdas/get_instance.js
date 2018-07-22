var AWS = require('aws-sdk');
var response = require('cfn-response');

exports.handler = function(event, context) {
    console.log("Request received:\n", JSON.stringify(event));

    var physicalId = event.PhysicalResourceId;

    function success(data) {
        data = data || {}
        console.log('SUCCESS:\n', data);
        return response.send(event, context, response.SUCCESS, data, physicalId);
    }

    function failed(err) {
        console.log('FAILED:\n', err);
        return response.send(event, context, response.FAILED, err, physicalId);
    }

    var spotFleetRequestId = event.ResourceProperties.SpotFleetRequestId;
    if (!spotFleetRequestId) {
        return failed('SpotFleetRequestId required');
    }

    var ec2 = new AWS.EC2();

    ec2.waitFor('instanceRunning', {
        'Filters': [{
            'Name': 'tag:aws:ec2spot:fleet-request-id',
            'Values': [spotFleetRequestId]
        }]
    })
    .promise()
    .then((data) => {
        console.log('"instanceRunning" Response:\n', JSON.stringify(data));

        var instance = data.Reservations[0].Instances[0];
        physicalId = instance.InstanceId;
        success({
            'PublicIpAddress': instance.PublicIpAddress,
            'AvailabilityZone': instance.Placement.AvailabilityZone
        });
    })
    .catch((err) => failed(err));
};

/*

{
    "Reservations": [
        {
            "Groups": [],
            "Instances": [
                {
                    "AmiLaunchIndex": 0,
                    "ImageId": "ami-5e8bb23b",
                    "InstanceId": "i-0069cd46e7763a0fe",
                    "InstanceType": "t2.small",
                    "KeyName": "training-us-east-2",
                    "LaunchTime": "2018-07-21T00:38:49.000Z",
                    "Monitoring": {
                        "State": "disabled"
                    },
                    "Placement": {
                        "AvailabilityZone": "us-east-2a",
                        "GroupName": "",
                        "Tenancy": "default"
                    },
                    "PrivateDnsName": "ip-172-31-13-239.us-east-2.compute.internal",
                    "PrivateIpAddress": "172.31.13.239",
                    "ProductCodes": [],
                    "PublicDnsName": "ec2-18-191-234-89.us-east-2.compute.amazonaws.com",
                    "PublicIpAddress": "18.191.234.89",
                    "State": {
                        "Code": 0,
                        "Name": "pending"
                    },
                    "StateTransitionReason": "",
                    "SubnetId": "subnet-33c66c5a",
                    "VpcId": "vpc-19558d70",
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "AttachTime": "2018-07-21T00:38:50.000Z",
                                "DeleteOnTermination": true,
                                "Status": "attaching",
                                "VolumeId": "vol-062fecc26b1fe5120"
                            }
                        }
                    ],
                    "ClientToken": "1c39ebe1-3122-4cde-bea8-3de4f7aaca10",
                    "EbsOptimized": false,
                    "EnaSupport": true,
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                        "Arn": "arn:aws:iam::466721095676:instance-profile/test18-LogRoleInstanceProfile-1S5RYSI2WRB9S",
                        "Id": "AIPAJ3DLIILWVSHPAYPBU"
                    },
                    "InstanceLifecycle": "spot",
                    "ElasticGpuAssociations": [],
                    "NetworkInterfaces": [
                        {
                            "Association": {
                                "IpOwnerId": "amazon",
                                "PublicDnsName": "ec2-18-191-234-89.us-east-2.compute.amazonaws.com",
                                "PublicIp": "18.191.234.89"
                            },
                            "Attachment": {
                                "AttachTime": "2018-07-21T00:38:49.000Z",
                                "AttachmentId": "eni-attach-96cb1c77",
                                "DeleteOnTermination": true,
                                "DeviceIndex": 0,
                                "Status": "attaching"
                            },
                            "Description": "",
                            "Groups": [
                                {
                                    "GroupName": "default",
                                    "GroupId": "sg-8ef54fe7"
                                }
                            ],
                            "Ipv6Addresses": [],
                            "MacAddress": "02:13:a0:fb:45:6e",
                            "NetworkInterfaceId": "eni-02910452",
                            "OwnerId": "466721095676",
                            "PrivateDnsName": "ip-172-31-13-239.us-east-2.compute.internal",
                            "PrivateIpAddress": "172.31.13.239",
                            "PrivateIpAddresses": [
                                {
                                    "Association": {
                                        "IpOwnerId": "amazon",
                                        "PublicDnsName": "ec2-18-191-234-89.us-east-2.compute.amazonaws.com",
                                        "PublicIp": "18.191.234.89"
                                    },
                                    "Primary": true,
                                    "PrivateDnsName": "ip-172-31-13-239.us-east-2.compute.internal",
                                    "PrivateIpAddress": "172.31.13.239"
                                }
                            ],
                            "SourceDestCheck": true,
                            "Status": "in-use",
                            "SubnetId": "subnet-33c66c5a",
                            "VpcId": "vpc-19558d70"
                        }
                    ],
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                        {
                            "GroupName": "default",
                            "GroupId": "sg-8ef54fe7"
                        }
                    ],
                    "SourceDestCheck": true,
                    "SpotInstanceRequestId": "sir-4wagsh2h",
                    "Tags": [
                        {
                            "Key": "aws:ec2spot:fleet-request-id",
                            "Value": "sfr-1ba3853c-8839-4e84-86a4-3f28f5f88ee8"
                        }
                    ],
                    "VirtualizationType": "hvm",
                    "CpuOptions": {
                        "CoreCount": 1,
                        "ThreadsPerCore": 1
                    }
                }
            ],
            "OwnerId": "466721095676",
            "RequesterId": "323427466144",
            "ReservationId": "r-0ba8762c3a38996f1"
        }
    ]
}

*/