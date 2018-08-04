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

    if (event.ResourceProperties.IgnoreFunction == 'true') {
        console.log('AMI not created (the function is ignored)');
        return success();
    }

    var ec2 = new AWS.EC2({region: event.ResourceProperties.Region});

    if (event.RequestType == 'Create' || event.RequestType == 'Update') {
        var instanceId = event.ResourceProperties.InstanceId;
        if (!instanceId) {
            return failed('InstanceId required');
        }

        var imageName = event.ResourceProperties.ImageName;
        if (!imageName) {
            return failed('ImageName required');
        }

        ec2.createImage({
            InstanceId: instanceId,
            Name: imageName
        })
        .promise()
        .then((data) => {
            console.log('Creating image:\n', JSON.stringify(data));

            physicalId = data.ImageId;

            var tagsPromise = ec2.createTags({
                Resources: [data.ImageId],
                Tags: [
                    {Key: 'spotty:stack-id', Value: event.StackId}
                ]
            }).promise()

            var imageAvailablePromise = ec2.waitFor('imageAvailable', {
                ImageIds: [data.ImageId]
            }).promise()

            return Promise.all([tagsPromise, imageAvailablePromise])
        })
        .then((data) => {
            console.log('Image tagged:\n', JSON.stringify(data[0]));
            console.log('Image available:\n', JSON.stringify(data[1]));
            console.log('Terminating the instance...');

            return ec2.terminateInstances({InstanceIds: [instanceId]}).promise()
        })
        .then((data) => {
            console.log('"terminateInstances" Response:\n', JSON.stringify(data));
            success();
        })
        .catch((err) => failed(err));

    } else if (event.RequestType == 'Delete') {
        if (!physicalId) {
            console.log('AMI ID not specified')
            return success();
        } else if (physicalId.indexOf('ami-') !== 0) {
            console.log('Physical ID is not an AMI ID')
            return success();
        }

        console.log('Searching AMI with ID=' + physicalId);

        ec2.describeImages({
            ImageIds: [physicalId]
        })
        .promise()
        .then((data) => {
            if (!data.Images.length) {
                throw new Error('No images found')
            }

            console.log('"describeImages" response:\n', data);

            return ec2.deregisterImage({
                ImageId: physicalId
            }).promise()
        })
        .then((data) => {
            console.log('Image deregistered:\n', data);

            return ec2.describeSnapshots({
                Filters: [{
                    Name: 'description',
                    Values: ['*' + physicalId + '*']
                }]
            }).promise()
        })
        .then((data) => {
            console.log('"describeSnapshots" response:\n', data);

            if (!data.Snapshots.length) {
                throw new Error('No snapshots found')
            }

            return ec2.deleteSnapshot({
                SnapshotId: data.Snapshots[0].SnapshotId
            }).promise()
        })
        .then((data) => {
            console.log('Snapshot deleted:\n', data);
            success()
        })
        .catch((err) => failed(err));
    }
};
