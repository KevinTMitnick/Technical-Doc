## Kafka 之监控

参考文档：https://zhuanlan.zhihu.com/p/127954833

### 0. Kafka Architecture

​	官方文档：https://kafka.apache.org/11/documentation/streams/architecture

![](/Users/kevintttccc/Desktop/Technical Doc/Kafka/KafkaArch.png)

### 1. 暴露 Kafka metric 的两种方式

默认情况下，Kafak metric 所有的指标都可以通过「JMX」 获取，两个方式介绍：

- Kafka Broker 外部：作为一个独立进程，通过 JMX 的 RMI 接口读取数据
  - 优点：调整不需要重启 Kafka Broker 进程
  - 缺点：多维护一下独立进程
- Kafka Broker 进程内读取 JMX 数据：这样解析数据的逻辑就在 Kafka Broker 进程内部, 如果有任何调整, 需要重启 Broker。
  - 缺点：调整需要重启 Broker

#### 1.1 jmx exporter 介绍

Prometheus 官方的组件「 jmx_exporter」 把两种实现都提供了：

- jmx_prometheus_httpserver：通过独立进程读取 JMX 的数据
- jmx_prometheus_javaagent：使用 Java Agent 方式, 尽量无侵入(在 kafka-server-start.sh 脚本中 增加 -javaagent 参数)的启动，读取 JMX 数据。

#### 1.2 jmx_prometheus_javaagent 收集 Kafak 指标

部署流程：

###### 第一步：下载 jmx_prometheus_javaagent、kafka.yml、zk.yml

javaagent 下载地址：https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/ 

Yaml 文件下载地址：https://github.com/prometheus/jmx_exporter/tree/master/example_configs

我们生产使用的 javaagent  版本号：

- jmx_prometheus_javaagent-0.11.0.jar

kafka.yml 文件内容：

```she
lowercaseOutputName: true
rules:
- pattern : kafka.network<type=(.+), name=(.+)TimeMs, request=(.+)><>99thPercentile
  name: kafka_network_$1_$2_total
  labels:
    request: "$3"
    kind: "99thpercentile"

- pattern : kafka.network<type=(.+), name=(.+)TimeMs, request=(.+)><>Mean
  name: kafka_network_$1_$2_total
  labels:
    request: "$3"
    kind: "mean"

- pattern : kafka.network<type=RequestMetrics, name=TotalTimeMs, request=(.+)><>Count
  name: kafka_network_requests_count_total
  labels:
    request: "$1"

- pattern : kafka.server<type=BrokerTopicMetrics, name=Bytes(.+)PerSec, topic=(.+)><>Count
  name: kafka_server_brokerTopicmetrics_bytes$1persec
  labels:
    topic: "$2"

- pattern : kafka.server<type=KafkaRequestHandlerPool, name=RequestHandlerAvgIdlePercent><>OneMinuteRat
  name: kafka_server_handlerpool_oneminute_rate
```

zk.yml 文件的内容：

```she
rules:
  # replicated Zookeeper
  - pattern: "org.apache.ZooKeeperService<name0=ReplicatedServer_id(\\d+)><>(\\w+)"
    name: "zookeeper_$2"
  - pattern: "org.apache.ZooKeeperService<name0=ReplicatedServer_id(\\d+), name1=replica.(\\d+)><>(\\w+)"
    name: "zookeeper_$3"
    labels:
      replicaId: "$2"
  - pattern: "org.apache.ZooKeeperService<name0=ReplicatedServer_id(\\d+), name1=replica.(\\d+), name2=(\\w+)><>(\\w+)"
    name: "zookeeper_$4"
    labels:
      replicaId: "$2"
      memberType: "$3"
  - pattern: "org.apache.ZooKeeperService<name0=ReplicatedServer_id(\\d+), name1=replica.(\\d+), name2=(\\w+), name3=(\\w+)><>(\\w+)"
    name: "zookeeper_$4_$5"
    labels:
      replicaId: "$2"
      memberType: "$3"
  # standalone Zookeeper
  - pattern: "org.apache.ZooKeeperService<name0=StandaloneServer_port(\\d+)><>(\\w+)"
    name: "zookeeper_$2"
  - pattern: "org.apache.ZooKeeperService<name0=StandaloneServer_port(\\d+), name1=InMemoryDataTree><>(\\w+)"
    name: "zookeeper_$2"
```

###### 第二步：编辑 kafka-server-start.sh 启动文件，添加 javaagent 路径

​		修改之后重启服务（提示⚠️：生产不要随便重启）

```she
$ cat $KAFKA_HOME/bin/kafka-server-start.sh 
......
export KAFKA_OPTS=-javaagent:/opt/jvm_agent/jmx_prometheus_javaagent-0.11.0.jar=7071:/opt/jvm_agent/kafka.yml
......
```

###### 第三步：编辑 Zookeeper 的 Env 文件：zkEnv.sh，追加监控 zk 的配置

​		修改之后重启服务（提示⚠️：生产不要随便重启）

```she
$ cat $ZK_HOME/bin/zkEnv.sh
...
SERVER_JVMFLAGS="-javaagent:/op t/jvm_agent/jmx_prometheus_javaagent-0.11.0.jar=7070:/opt/jvm_agent/zk.yml"
...
```



### 2. 主要指标维度

​	一个功能健全的kafka集群可以处理相当大的数据量，由于消息系统是很多大型应用的基石，因此broker集群在性能上的缺陷，都会引起整个应用栈的各种问题。

​	Kafka 的度量指标主要从五个维度讨论 Kafak 监控：

	- Kafka 集群所在主机监控
	- Kafka 「Broker」性能
	- Kafka 「Broker JVM」 指标
	- Kafka 客户端：生产者「Producer」、消费者「Comsumer」
	- 服务器之间的交互行为

​	另外，在 Kafka 2.8 之前的版本，依赖 Zookeeper 来维护集群状态，所以 Zookeeper 性能的监控也成为整个 Kafka 监控计划中的一部分。

#### 2.1 主机监控

参考文档：《Systems Performance》一书

主机的监控维度有：

- **机器负载**： Load
- **CPU**：CPU 使用率
- **Memory**：内存使用率，包括「Free Memory」和「Used Memory」
- **Network I/O**：网络 「In/Out」指标
- **TCP**：TCP 连接数
- **Disk Usage**：磁盘空间使用率
- **Disk QPS**：磁盘 I/O，「读/写」使用率
- **Disk Busy Time**：
- **Inode 使用情况**：主机的「Inode」数量使用情况

案例：



#### 2.2 JVM 监控

参考文档：《Java Performance》一书                                      										                      Java GC：    https://www.oracle.com/webfolder/technetwork/tutorials/obe/java/gc01/index.html

​	Kafka 本身是一个普通的 Java 进程，所以需要依赖 Java 的垃圾回收机制来释放内存，如果kafka集群越活跃，则垃圾回收的频率也就越高。

​	首先了解 Kafka Broker Jvm 的 Gc `频率` 和 `延时` 都是多少，每次 Gc 后存活对象的大小是怎么样的等。了解了这些信息，后续才能明确调优方向。

JVM 监控的维度有：

- Jvm Memory Used：jvm memory 使用情况
- Jvm Gc 频率
- Jvm Gc 延时

#### 2.3 Kafka 系统监控

##### 2.3.0 Broker 关键日志

- **Broker 服务器日志**：server.log
  - Broker 端有严重错误或者故障的时候，通过 `server.log` 来定位故障原因
- **Controller 日志**：控制器 controller.log
- **Topic、Partition 状态变更日志**：state-change.log

##### 2.3.1 Kafka 总体监控

在 Kafka 2.8 之前，Kafka 还是依赖 Zookeeper 来维护集群状态，所以从 Kafka 系统本身的监控维度有：

- zookeeper 上  /kafka/broker/ids 目录下节点数量
- leaders 数量
- replica 数量
- ISR 数量（in sync replica）

##### 2.3.2 Broker 度量指标

​	Kafka 的服务端度量指标是为了监控 Broker，也是整个消息系统的核心。因为所有消息都通过 Kafka Broker 传递，然后被消费，所以对于 Broker 集群上出现的问题的 `监控` 和 `告警` 就尤为重要。Broker 性能指标有一下三类：

​	Broker 监控维度有：

- Broker 进程是否启动状态
- Broker 是否提供服务
- Broker 日志
  - Broker 服务器日志
  - Kafka controller 日志
- 数据流量：流入速度、流出速度（message/sec、byte/sec）

##### 2.3.3 ActiveControllerCount 

参考文档：https://blog.csdn.net/u013256816/article/details/80865540

​	在 Kafka 集群中会有一个或者多个 Broker，其中有一个 broker 会被选举为控制器（Kafka Controller），它负责管理整个集群中所有分区和副本的状态。当某个分区的 Leader 副本出现故障时，由控制器负责为该分区选举新的 leader 副本。当检测到某个分区的 ISR 集合发生变化时，由控制器负责通知所有 broker 更新其元数据信息。当使用 kafka-topics.sh 脚本为某个 topic 增加分区数量时，同样还是由控制器负责分区的重新分配。

​	在 Kafka 2.8 版本之前，控制器选举的工作依赖于  Zookeeper，成功竞选为控制器的 broker 会在 Zookeeper 中创建 「/controller」这个临时（EPHEMERAL）节点，此临时节点的内容参考如下：

```shell
{"version":1,"brokerid":0,"timestamp":"1529210278988"}
```

注释：																																		      	     其中 「version」 在目前版本中固定为 1，「brokerid」 表示称为控制器的broker 的 「id编号」，「timestamp」表示竞选称为控制器时的时间戳。

​	在任意时刻，集群中有且仅有一个控制器。每个 broker 启动的时候会去尝试去读取「/controller」节点的 brokerid 的值，如果读取到 brokerid 的值不为「-1」，则表示已经有其它 broker 节点成功竞选为控制器，所以当前 broker 就会放弃竞选。

​	正常情况下，Controller 所在 Broker 上的这个 JMX 指标值应该是 1，其他 Broker 上的这个值是 0。如果你发现存在多台 Broker 上该值都是 1 的情况，一定要赶快处理，处理方式主要是查看网络连通性。这种情况通常表明集群出现了脑裂。脑裂问题是非常严重的分布式故障，Kafka 目前依托 ZooKeeper 来防止脑裂。但一旦出现脑裂，Kafka 是无法保证正常工作的。

##### 2.3.4 Topic 监控

Topic 监控维度：

- 数据量大小：offset
- 数据流量：流入速度、流出速度（message/sec、byte/sec）

由于流入数据速度(byte)决定了数据量大小，流入message速度决定offset，所以监控流入速度，流入message，流入速度就足够了

##### 2.3.5 Partition 监控

Partition 监控维度：

- 数据量大小：offset
- 数据流量：流入速度、流出速度（message/sec、byte/sec）

##### 2.3.6 Producer 监控

Producer 监控维度：

- producer 队列中排队请求数量
- request-latency：即消息生产请求的延时，表述了 Producer 程序的 TPS
- QPS / 分钟

##### 2.3.7 Consumer group 监控

参考：[消费者组消费进度监控](file:///Users/kevintttccc/Desktop/Kafka%20HTML/23.%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%AE%9E%E8%B7%B5%E5%8F%8A%E5%8E%9F%E7%90%86%E5%89%96%E6%9E%90%EF%BD%9C%E6%B6%88%E8%B4%B9%E8%80%85%E7%BB%84%E6%B6%88%E8%B4%B9%E8%BF%9B%E5%BA%A6%E7%9B%91%E6%8E%A7%E9%83%BD%E6%80%8E%E4%B9%88%E5%AE%9E%E7%8E%B0.html)

Consumer 监控维度：

- Lag 值 = 「Producer 产生的消息数」 - 「Consumer 消费了的消息数量」
- consumer 队列中排队请求数量
- records-lag：请求响应时间
- 最近一分钟平均每秒请求书

对于 Kafka 消费者来说，最重要的事情就是监控它们的「**消费进度**」，或者说是监控「**滞后程度**」，对于「滞后程度」使用专门的名词：`消费者 Lag` 或者 `Consumer Lag`
