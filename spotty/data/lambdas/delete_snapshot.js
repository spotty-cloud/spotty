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

    // ignore non-delete requests
    if (event.RequestType !== 'Delete') {
        console.log('Non-delete request is ignored');
        return success();
    }

    var snapshotId = event.ResourceProperties.SnapshotId;
    if (!snapshotId) {
        return failed('SnapshotId required');
    }

    var ec2 = new aws.EC2({region: event.ResourceProperties.Region});

    ec2.describeSnapshots({Filters: [{Name: 'snapshot-id',  Values: [snapshotId]}]})
    .promise()
    .then((data) => {
        console.log('"describeSnapshots" response:\n', JSON.stringify(data));

        if (!data.Snapshots.length) {
            console.log('Snapshot not found');
            return null;
        }

        return ec2.deleteSnapshot({SnapshotId: snapshotId}).promise();
    })
    .then((data) => {
        console.log('"deleteSnapshot" response:\n', JSON.stringify(data));
        success();
    })
    .catch((err) => failed(err));
};
