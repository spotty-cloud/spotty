# Instance Parameters

Instance parameters are part of the [configuration file], but for each provider they are different. 
Here you can find parameters for a remote instance:

- __`containerName`__ _(optional)_ - a name of the container from the `containers` section.
Default value: `default`.

- __`volumes`__ _(optional)_ - the list of volumes to attach to the instance:
    - __`name`__ - a name of the volume. This name should match one of the container's `volumeMounts` to have this 
    volume attached to the container's filesystem.

    - __`parameters`__ _(optional)_ - parameters of the volume:
        - __`path`__ _(optional)_ - a path on a remote instance that should be mounted to the container.

[configuration file]: </docs/user-guide/configuration-file>
