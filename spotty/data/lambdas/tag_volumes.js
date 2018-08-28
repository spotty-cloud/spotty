var aws = require('aws-sdk');
var response = require('cfn-response');

exports.handler = function(event, context) {
    console.log("Request received:\n", JSON.stringify(event));

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

    // ignore non-create requests
    if (event.RequestType !== 'Create') {
        console.log('Non-create request is ignored');
        return success();
    }

    var instanceId = event.ResourceProperties.InstanceId;
    if (!instanceId) {
        return failed('InstanceId required');
    }

    var ec2 = new aws.EC2({region: event.ResourceProperties.Region});

    ec2.describeInstances({InstanceIds: [instanceId]})
    .promise()
    .then((data) => {
        console.log('"describeInstances" response:\n', JSON.stringify(data));

        var instance = data.Reservations[0].Instances[0],
            blockDevices = instance.BlockDeviceMappings,
            tagPromises = [];

        for (var i = 0; i < blockDevices.length; i++) {
            var tagPromise = ec2.createTags({Resources: [blockDevices[i].Ebs.VolumeId], Tags: [
                {Key: 'spotty:stack-id', Value: event.StackId},
                {Key: 'spotty:volume:device', Value: blockDevices[i].DeviceName},
                {Key: 'spotty:volume:delete-on-termination', Value: String(blockDevices[i].Ebs.DeleteOnTermination)}
            ]}).promise();

            tagPromises.push(tagPromise)
        }

        return Promise.all(tagPromises);
    })
    .then((data) => {
        console.log('"createTags" responses:\n', JSON.stringify(data));
        success();
    })
    .catch((err) => failed(err));
};
