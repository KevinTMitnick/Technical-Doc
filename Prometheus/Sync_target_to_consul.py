```py
import consul
import json
import os
import requests
import traceback


# consul_host = '127.0.0.1'
consul_host = 'consul_ha.example.com'
consul01_host = 'consul01.example.com'
consul02_host = 'consul02.example.com'
consul03_host = 'consul03.example.com'

c = consul.Consul(host=consul_host)
c01 = consul.Consul(host=consul01_host)
c02 = consul.Consul(host=consul02_host)
c03 = consul.Consul(host=consul03_host)

push_gateway_url = 'http://prometheus.gateway.com/metrics/upload'

target_map = {
    "redis-prod-ms-rcmdsys": "/home/ec2-user/prometheus/prometheus/conf/redis-prod-ms-rcmdsys.json"	#内容看注释
}


def push_alert_metric(service_name):
    payload = [{"tags": {"business_group": "platform", "status": "failed",
                         "service_name": service_name}, "type": ["once"], "name":"sync_target_to_consul", "value":1}]
    try:
        requests.post(push_gateway_url, json=payload)
    except Exception:
        print(traceback.print_exc())


def update_consul_service(service_name, data):
    old_id_list = [item["ServiceID"] for item in c.catalog.service(
        service_name)[1]]
    new_id_list = data.get("targets", [])

    delete_list = set(old_id_list).difference(set(new_id_list))
    add_list = set(new_id_list).difference(set(old_id_list))

    print(delete_list)
    print(add_list)

    for service_id in delete_list:
        c01.agent.service.deregister(service_id)
        c02.agent.service.deregister(service_id)
        c03.agent.service.deregister(service_id)

    labels_map = data.get("labels_map", {})
    for service_id in add_list:
        labels = labels_map.get(service_id, {})
        tags = []
        for k, v in labels.items():
            tag_str = f'{k}={v}'
            tags.append(tag_str)
        address = service_id.split(":")[0]
        port = int(service_id.split(":")[1])
        c.agent.service.register(
            service_name, service_id, address, port, tags,
            enable_tag_override=True
        )


def sync_target_to_consul():
    for k, v in target_map.items():
        if os.path.exists(v):
            service_name = k
            file_path = v
            with open(file_path) as f:
                data = json.load(f)
                data1 = {"targets": [], "labels_map": {}}
                data2 = {"targets": [], "labels_map": {}}
                for item in data:
                    target_list = item.get("targets", [])
                    labels = item.get("labels", {})
                    for target in target_list:
                        if "172.21" in target:
                            data1["targets"].append(target)
                            data1["labels_map"].update({target: labels})
                        else:
                            data2["targets"].append(target)
                            data2["labels_map"].update({target: labels})
                try:
                    update_consul_service(f'{service_name}-172-21', data1)
                    update_consul_service(service_name, data2)
                except Exception:
                    push_alert_metric(service_name)


if __name__ == "__main__":
    sync_target_to_consul()
```

注释：

redis-prod-ms-rcmdsys.json 的文件格式：

```pytho
[
    {
        "labels": {
            "instance_type": "m6g.xlarge",
            "business_group": "matrix",
            "addr": "prod-ms-rcmdsys.001.redis.example.com:6379"
        },
        "targets": ["172.16.1.10:9121"]
    }
]
```

