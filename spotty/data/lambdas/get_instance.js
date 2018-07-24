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

    // ignore delete request
    if (event.RequestType === 'Delete') {
        console.log('Delete request is ignored');
        return success();
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
