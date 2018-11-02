var aws = require("aws-sdk");
var response = require('cfn-response');

exports.handler = function(event, context) {
    console.log("request received:\n" + JSON.stringify(event));

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

    // ignore delete request
    if (event.RequestType == 'Delete') {
        console.log('Delete request is ignored');
        return success();
    }

    var ec2 = new aws.EC2({region: event.ResourceProperties.Region});

    // get AMI IDs with the specified name pattern and owner
    ec2.describeImages({
        Filters: [{ Name: "name", Values: ['ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64*']}],
        Owners: ['099720109477']
    })
    .promise()
    .then((data) => {
        console.log('Number of found images: ', data.Images.length);

        var images = data.Images;

        // sort images by name in descending order (the names contain the AMI version, formatted as YYYYMMDD.Ver)
        images.sort(function(x, y) { return y.Name.localeCompare(x.Name); });

        var amiId = false;
        for (var j = 0; j < images.length; j++) {
            if (isBeta(images[j].Name)) continue;
            amiId = images[j].ImageId;
            break;
        }

        if (!amiId) {
            throw new Error('AMI not found');
        }

        console.log('Found AMI ID=' + amiId)

        physicalId = amiId;
        success();
    })
    .catch((err) => failed(err));
};

// Check if the image is a beta or rc image. The Lambda function won't return any of those images.
function isBeta(imageName) {
    return imageName.toLowerCase().indexOf("beta") > -1 || imageName.toLowerCase().indexOf(".rc") > -1;
}
