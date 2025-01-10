# MID Server

## Overview

MID Server is a Java application that runs as a Windows service or UNIX daemon on a server. It is used to connect to instances and execute automation tasks. MID Servers can be used to run probes and sensors, which are small programs that collect data from devices and applications. MID Servers can also be used to run integration hubs, which are programs that connect to external systems and run scripts to collect data. MID Servers can be used to run orchestration activities, which are programs that automate tasks across multiple systems. For more information, see the [ServiceNow documentation](https://www.servicenow.com/docs/pt-BR/bundle/washingtondc-servicenow-platform/page/product/mid-server/concept/mid-server-landing.html).

This path contains the MID Server installation files and the configuration files used in the MID Server instance to run in a docker container. If necessary, you can download the MID Server installation files from the ServiceNow instance.

## Files not included from security reasons

The following files are not included in this path due to security reasons:
file | description
--- | ---
.env | File that contains the docker tag environment variable
mid-secrets.properties | File that contains the MID Server secrets (not used in my case)
mid.env | File that contains the MID Server environment variables


## Exemplary files

### .env

```env
DOCKER_TAG=mid:xanadu-07-02-2024__patch4-11-22-2024_12-02-2024_1408
```

### mid-secrets.properties

```properties
mid.instance.password={{mid_instance_password}}
mid.proxy.password={{mid_proxy_password}}
```

### mid.env

```env
MID_INSTANCE_URL=https://{{instance_url}}
MID_INSTANCE_USERNAME={{instance_username}}
MID_INSTANCE_PASSWORD={{instance_password}}
MID_SECRETS_FILE={{BLANK - Not used}}
MID_SERVER_NAME={{mid_server_name}}
MID_PROXY_HOST={{BLANK - Not used}}
MID_PROXY_PORT={{BLANK - Not used}}
MID_PROXY_USERNAME={{BLANK - Not used}}
MID_PROXY_PASSWORD={{BLANK - Not used}}
MID_MUTUAL_AUTH_PEM_FILE={{BLANK - Not used}}
MID_SSL_BOOTSTRAP_CERT_REVOCATION_CHECK={{BLANK - Not used}}
MID_SSL_USE_INSTANCE_SECURITY_POLICY={{BLANK - Not used}}
