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

    // ignore non-create requests
    if (event.RequestType !== 'Create') {
        console.log('Non-create request is ignored');
        return success();
    }

    var logGroupName = event.ResourceProperties.LogGroupName;
    if (!logGroupName) {
        return failed('LogGroupName required');
    }

    var retentionInDays = event.ResourceProperties.RetentionInDays;
    if (!retentionInDays) {
        return failed('RetentionInDays required');
    }

    var cloudwatchlogs = new aws.CloudWatchLogs();

    cloudwatchlogs.putRetentionPolicy({
        logGroupName: logGroupName,
        retentionInDays: retentionInDays
    })
    .promise()
    .then((data) => {
        console.log('"putRetentionPolicy" Response:\n', JSON.stringify(data));
        success();
    })
    .catch((err) => failed(err));
};
