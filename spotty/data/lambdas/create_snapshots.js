var aws = require('aws-sdk');
var response = require('cfn-response');

exports.handler = function(event, context) {
    console.log('Request received:\n', JSON.stringify(event));

    var physicalId = event.PhysicalResourceId;

    function success(data) {
        data = data || {};
        console.log('SUCCESS:\n', data);

        // temporary delay in response to get the logs
        setTimeout(function() {
            response.send(event, context, response.SUCCESS, data, physicalId);
        }, 5000);
    }

    function failed(err) {
        console.log('FAILED:\n', err);

        // temporary delay in response to get the logs
        setTimeout(function() {
            response.send(event, context, response.FAILED, err, physicalId);
        }, 5000);
    }

    // ignore non-delete requests
    if (event.RequestType !== 'Delete') {
        console.log('Non-delete request is ignored');
        return success();
    }

    var devices = event.ResourceProperties.Devices;
    if (!devices) {
        console.log('Devices not specified');
        return success();
    }

    var ec2 = new aws.EC2({region: event.ResourceProperties.Region});

    ec2.describeVolumes({
        Filters: [
            {Name: 'tag:spotty:stack-id', Values: [event.StackId]},
            {Name: 'tag:spotty:volume:delete-on-termination', Values: ['false']}
        ]
    })
    .promise()
    .then((data) => {
        console.log('"describeVolumes" response:\n', JSON.stringify(data));

        var volumePromises = [];
        for (var i = 0; i < data.Volumes.length; i++) {
            var volume = data.Volumes[i],
                deviceName = volume.Tags.filter(function (el) {
                    return el.Key == 'spotty:volume:device';
                })[0].Value;

            if (!(deviceName in devices)) {
                throw 'Device "' + deviceName + '" not found';
            }

            var mode = devices[deviceName].mode,
                snapshotName = devices[deviceName].snapshotName,
                origSnapshotId = devices[deviceName].snapshotId;

            // create new snapshot
            var snapshotPromise = ec2.createSnapshot({VolumeId: volume.VolumeId})
                .promise()
                .then((data) => {
                    console.log('"createSnapshot" response:\n', JSON.stringify(data));
                    return ec2.waitFor('snapshotCompleted', {SnapshotIds: [data.SnapshotId]}).promise();
                });

            // modify tag or delete original snapshot
            var origSnapshotPromise = snapshotPromise.then((data) => {
                console.log('"snapshotCompleted" response:\n', JSON.stringify(data));

                if (data.Snapshots[0].State != 'completed') {
                    throw 'Snapshot is not completed';
                }

                var describeSnapshotsPromise;

                // check if the snapshot wasn't already deleted
                if (origSnapshotId) {
                    describeSnapshotsPromise = ec2.describeSnapshots({
                        Filters: [{Name: 'snapshot-id',  Values: [origSnapshotId]}]
                    })
                    .promise()
                    .then((data) => {
                        console.log('"describeSnapshots" response:\n', JSON.stringify(data));

                        var updateSnapshotPromise;

                        if (data.Snapshots.length) {
                            switch (mode) {
                                case 'update':
                                    updateSnapshotPromise = ec2.deleteSnapshot({SnapshotId: origSnapshotId}).promise();
                                    break;
                                case 'create':
                                    updateSnapshotPromise = ec2.createTags({
                                        Resources: [origSnapshotId],
                                        Tags: [{Key: 'Name', Value: snapshotName + '-' + Math.floor(Date.now() / 60000)}],
                                    }).promise();
                                    break;
                                default:
                                    throw 'Mode "' + mode + '" not supported';
                            }
                        } else {
                            console.log('Original snapshot not found');
                        }

                        return updateSnapshotPromise;
                    });
                } else {
                    console.log('Original snapshot not specified');
                }

                return describeSnapshotsPromise;
            });

            // tag new snapshot and delete the volume
            var volumePromise = Promise.all([snapshotPromise, origSnapshotPromise])
                .then(function(data) {
                    var snapshotsResp = data[0];
                    return ec2.createTags({
                        Resources: [snapshotsResp.Snapshots[0].SnapshotId],
                        Tags: [{Key: 'Name', Value: snapshotName}]
                    }).promise();
                }).then((data) => {
                    ec2.deleteVolume({VolumeId: volume.VolumeId});
                });

            volumePromises.push(volumePromise);
        }

        return Promise.all(volumePromises);
    }).then((data) => {
        console.log('"deleteVolume" responses:\n', JSON.stringify(data));
        success();
    })
    .catch((err) => failed(err));
};
