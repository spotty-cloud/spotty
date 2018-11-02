var aws = require('aws-sdk');
var response = require('cfn-response');

exports.handler = function(event, context) {
    console.log('Request received:\n', JSON.stringify(event));

    var physicalId = event.PhysicalResourceId;

    function success(data) {
        data = data || {};
        console.log('SUCCESS:\n', data);
        return response.send(event, context, response.SUCCESS, data, physicalId);
    }

    function failed(err) {
        console.log('FAILED:\n', err);
        return response.send(event, context, response.FAILED, err, physicalId);
    }

    var ec2 = new aws.EC2({region: event.ResourceProperties.Region});

    if (event.RequestType == 'Create' || event.RequestType == 'Update') {
        ec2.describeImages({Filters: [{Name: 'tag:spotty:stack-id',  Values: [event.StackId]}]})
        .promise()
        .then((data) => {
            if (!data.Images.length) {
                throw new Error('No images found');
            }

            console.log('"describeImages" response:\n', data);

            // set physical resource ID to AMI ID
            physicalId = data.Images[0].ImageId;
            success();
        })
        .catch((err) => failed(err));
    } else {
        var imageId = physicalId;

        console.log('Searching AMI with ID=' + imageId);

        ec2.describeImages({ImageIds: [imageId]})
        .promise()
        .then((data) => {
            if (!data.Images.length) {
                throw new Error('No images found');
            }

            console.log('"describeImages" response:\n', data);

            return ec2.deregisterImage({ImageId: imageId}).promise();
        })
        .then((data) => {
            console.log('Image deregistered:\n', data);

            return ec2.describeSnapshots({
                Filters: [{
                    Name: 'description',
                    Values: ['*' + imageId + '*']
                }]
            }).promise();
        })
        .then((data) => {
            console.log('"describeSnapshots" response:\n', data);

            if (!data.Snapshots.length) {
                throw new Error('No snapshots found');
            }

            return ec2.deleteSnapshot({SnapshotId: data.Snapshots[0].SnapshotId}).promise();
        })
        .then((data) => {
            console.log('Snapshot deleted:\n', data);
            success();
        })
        .catch((err) => failed(err));
    }
};
