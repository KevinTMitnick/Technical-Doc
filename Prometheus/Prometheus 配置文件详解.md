官方文档：

​		https://prometheus.io/docs/prometheus/latest/configuration/configuration/

# 1. 三大配置模块

```she
global:									# Prometheus 服务全局配置
  scrape_interval:			15s		# 配置抓去时间间隔
  evaluation_interval:	15s		# 告警检测时间间隔

rule_files:							# 指定告警规则文件
	- first.rules
	- seconed.fules

scrape_configs:						# 指定 Prometheus 要监控的目标
  - job_name: prometheus	# Job 名称（可以有多个）
    static_configs:
      - targets: ['localhost:9090']
```

# 2. scrape_configs 配置介绍

## 2.1 kubernetes_sd_config

参考文档：https://prometheus.io/docs/prometheus/latest/configuration/configuration/#kubernetes_sd_config

### role 介绍

kubernetes_sd_config 中有 5 种角色：

- endpoints
- node
- service
- ingress
- pod



### 2.1.1 role-node

​		prometheus.yml 配置如下：

```shel
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

scrape_configs:
- job_name: 'kubernetes-nodes'
  kubernetes_sd_configs:
  - role: node
```

​		该 `node` 角色为每个集群节点发现一个目标，其地址默认为 Kubelet 的 HTTP 端口。目标地址默认为 Kubernetes 节点对象的第一个现有地址，地址类型顺序为 `NodeInternalIP`、`NodeExternalIP`、 `NodeLegacyHostIP`、`NodeHostName`。

##### 可选 labels

```shell
__meta_kubernetes_node_name:	节点名称
__meta_kubernetes_node_label_<labelname>: node 的 labels 标签
__meta_kubernetes_node_annotation_<annotationname>: node 的注释
__meta_kubernetes_node_address_<address_type>: 每个节点地址类型（如果存在NodeInternalIP, NodeExternalIP, NodeLegacyHostIP, and NodeHostName其中一个）
```

此外，`instance` 节点的标签将设置为从 api-server 检索到的节点名称。

### 2.1.2 cadvisor

#### 什么是 cadvisor？

`cadvisor` 已经被集成在 kubelet 中，所以发现了 node 就相当于发现了 cadvisor。通过 `cadvisor` 能够获取当前节点上运行的所有容器的资源使用情况，通过 `/api/v1/nodes/${1}/proxy/metrics/cadvisor` 采集容器指标

#### 配置

​		prometheus.yml 配置如下：

```shel
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

scrape_configs:
- job_name: 'kubernetes-cadvisor'
  kubernetes_sd_configs:
  - role: node
```

### 2.1.3 role-service

​		prometheus.yml 配置如下：

```shel
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

scrape_configs:
- job_name: 'kubernetes-services'
  kubernetes_sd_configs:
  - role: service
```

##### 可选 labels

```she
__meta_kubernetes_namespace: service 所处的 namespace
__meta_kubernetes_service_name: serviceName
__meta_kubernetes_service_label_<labelname>: service 的label
__meta_kubernetes_service_annotation_<annotationname>: service 的描述信息
__meta_kubernetes_service_port_name: service 的 portName
__meta_kubernetes_service_port_number: service 的端口
__meta_kubernetes_service_port_protocol: 协议
```

### 2.1.4 role-ingress

​		prometheus.yml 配置如下：

```shel
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

scrape_configs:
- job_name: 'kubernetes-ingress'
  kubernetes_sd_configs:
  - role: ingress
```

##### 可选 lables

```shell
__meta_kubernetes_namespace: ingress 的 namespace
__meta_kubernetes_ingress_name: ingressName
__meta_kubernetes_ingress_label_<labelname>: ingress 的 label
__meta_kubernetes_ingress_annotation_<annotationname>: ingress 的 annotation
__meta_kubernetes_ingress_scheme: 默认是 http, https 
__meta_kubernetes_ingress_path: Path from ingress spec. Defaults to /
```



### 2.1.5 role-pods

​		prometheus.yml 配置如下：

```shell
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
```

##### 可选 labels

```shell
__meta_kubernetes_namespace: pod 所在的 namespace.
__meta_kubernetes_pod_name: podName
__meta_kubernetes_pod_ip: podIP
__meta_kubernetes_pod_label_<labelname>: pod 的 label
__meta_kubernetes_pod_annotation_<annotationname>: pod 的annotation 
__meta_kubernetes_pod_container_name: 容器名称
__meta_kubernetes_pod_container_port_name: 容器端口名称
__meta_kubernetes_pod_container_port_number: 容器端口号
__meta_kubernetes_pod_container_port_protocol: 容器的协议
__meta_kubernetes_pod_ready: pod 的状态「ture/false」
__meta_kubernetes_pod_node_name: 所在的节点名称
__meta_kubernetes_pod_host_ip: pod 所在节点的 IP
__meta_kubernetes_pod_uid: pod 的 UUID
```



### 2.1.6 role-endpoints

​		prometheus.yml 配置如下：

```shell
global:
  scrape_interval:     15s 
  evaluation_interval: 15s

scrape_configs:
- job_name: 'kubernetes-endpoints'
  kubernetes_sd_configs:
  - role: endpoints
```

##### 可选 labels

```shell
__meta_kubernetes_namespace: endpoints 的 namespace
__meta_kubernetes_endpoints_name: endpoints 的 name
__meta_kubernetes_endpoint_ready: endpoint 状态「true/false」
__meta_kubernetes_endpoint_port_name: endpoint port Name 
__meta_kubernetes_endpoint_port_protocol: 协议
```

## 2.2 relabel_configs 详解

#### 简介

```shell
relabel_configs:

  source_labels: 	
  separator:
  target_label:
  regex:
  replacement:
  action:
```

- source_labels: 引用标签，源标签
  - 作用对象：P8S 内部的 [元标签]
  - 引用目的：
    - 删除: 删掉标签
    - 修改: 修改源标签的值
    - 引用: 引用之后创建新标签「target_label」
- separator: 指定指定「replacement」的  `连接符`
  - 作用对象：[source_labels]，[replacement]
  - 作用：指定每个「replacement」之间的 `连接符`，默认是: 分号(;)，空表示不使用任何符号
- target_label: 存在替换，没有新建
  - 作用对象：[source_labels] 和 [regex]
  - 作用：
- regex：
  - 作用对象：[source_labels]
  - 正则表达式配置方法：
    - () 进行分组:  
      - 案例：([0-9]*)([a-z] *)，第一组就是 `$1`,  第二组就是 `$2`
- replacement: 占位符
  - 作用对象：[regex]
  - 作用：对「regex」的分组进行拼接
    - 一个 `regex` 的 `()` 对应一个占位符
    - 第一个 `()` 表示：`$1`，第二个`()` 表示 `$2`，依此类推
- action: 
  - 作用对象: [source_labels ]  和 [target_label]
  - 作用：
  - 选项：
    - replace
    - drop

#### 标签管理

##### 替换标签值 - replace

- replace: 

  - 首先，`串联`  [source_labels] 指定的各标签值
  - 而后，[regex] 中的 `正则表达式` 对 `源标签 值` 进行匹配判断
  - 最后，匹配到的值替换为 [replacement] 字段中保存的值。

  根据「regex」配置，匹配「source_labels」标签的值（⚠️ 多个 source_labels 的值按照 separator 进行拼接），并将匹配到的值写入到「target_label」中，多个匹配组，可以使用 `${1}`, `${2}` 确定写入内容

- hashmod: 不常用，不做详细介绍

##### 删除指标 - keep、drop

- 说明：该配置每个「指标名字」对应一个 `target`

- keep: 「regex」`没有匹配` 匹配到「source_labels」的 `各指标串联值` 时，删除该 `Target` 
- drop: 「regex」`匹配` 匹配到「source_labels」的 `各指标串联值 `时，删除该 `Target` 

##### 创建或删除标签 - labelmap、labeldrop、labelkeep

- labelmap: 

  - 作用对象：所有「Target 的标签」（所有使用的时候，可以不用指定 source_labels）

  - 作用：`把原来的 label 映射为新的 label`。根据「regex」去匹配 `Target` 实例所有标签的 `名称`，基于 `已经存在标签`，重新生成一个新的标签名，而后将匹配到的标签赋值给 `replacement` 字段指定的标签名称之上（所以在这里 replacement 就不是占位符的值，而是 [新标签名]）。

  - 示例：

    ```shell
    relabel_configs:
    - regex: "(job|app)"   #匹配所有由 job和app 的标签 
      replacement: ${1}_name #标签重命名,加后缀 _name
      action: labelmap
      
    # 生成结果，如下所示：
    Labels:
    	app="node-exporter"
    	app_name="node-exporter"
    	job="nodes"
    	job_name="nodes"
    ```

    

- labelkeep: 对 Target 标签进行过滤，会移除不匹配过滤条件的所有标签

- labeldrop: 对 Target 标签进行过滤，会移除匹配过滤条件的所有标签

#### relabel_configs 示例

##### replcace 示例-操作标签的 [值]

下面示例，将三个源标签的值接顺序串联后，由指定的正则表达式进行「模式匹配」，而后由「replacement」引用模式匹配的结果，并加以改造后，将其赋值给 `endpoint` 标签

```shell
- job_name: 'nodes'
  file_sd_config:
  - files:
    - targets/prometheus/node*.yaml
    
  relabel_configs:
  - source_labels:
    - __scheme__
    - __address__
    - __metrics_path__
    
    regex: "(http|htttps)(.*)"
    separator: ""
    target_label: "endpoint"
    replacement: "${1}://${2}"
    action: replace
```

生成的结果如下：

```shell
Labels:
    endpoint="https://localhost:9100/metrics"
```

如果不指定 `separator`，结果显示如下：

```shell
Labels:
	endpoint="https://;localhost:9100;/metrics"	

# 说明：可以看到，source_labels 之间有一个 ';' 分号分隔
```

##### labelmap 示例-[操作标签的名]

背景：对已经存在的 job、app 标签加一个后缀 `_name`， 并删除原标签名 job 和 app；

加后缀配置示例：

```shell
relabel_configs:
- regex: "(job|app)"   		#匹配所有由 job和app 的标签 
  replacement: ${1}_name 	#标签重命名,加后缀 _name
  action: labelmap
```

​		生成结果，如下所示：

```shell
Labels:
	app="node-exporter"
	app_name="node-exporter"
	job="nodes"
	job_name="nodes"
```

加后缀 + 删除原标签配置示例：

```shell
relabel_configs:
- regex: "(job|app)"   		# 匹配所有由 job和app 的标签 
  replacement: ${1}_name 	# 标签重命名,加后缀 _name
  action: labelmap
  

- regex: "(job|app)"
  action: labeldrop				# 删除标签
```

​	



