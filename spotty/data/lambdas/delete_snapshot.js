var aws = require("aws-sdk");
var response = require('cfn-response');

exports.handler = function(event, context) {
    console.log("request received:\n" + JSON.stringify(event));

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

    // ignore non-delete requests
    if (event.RequestType !== 'Delete') {
        console.log('Non-delete request is ignored');
        return success();
    }

    var snapshotId = event.ResourceProperties.SnapshotId;
    if (!snapshotId) {
        console.log('Nothing to delete');
        return success();
    }

    var ec2 = new aws.EC2({region: event.ResourceProperties.Region});

    ec2.deleteSnapshot({SnapshotId: snapshotId})
    .promise()
    .then((data) => {
        console.log('"deleteSnapshot" Response:\n', JSON.stringify(data));
        success();
    })
    .catch((err) => failed(err));
};
