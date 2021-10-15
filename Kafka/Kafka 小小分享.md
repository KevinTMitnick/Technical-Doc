## Kafka 是什么？

- 流式消息系统

## Kafka 组成

- Producer：消息生产者
- Broker：Kakfa 的节点
- Consumer：消息消费者
- Consumer Group：消费组，由多个 Consumer 组成
- Zookeeper：为 Kafka 提供元数据管理、Leader 选举

![image-20210708095436090](/Users/kevintttccc/Library/Application Support/typora-user-images/image-20210708095436090.png)

## Kafak 数据如何存储的？

![image-20210708095519734](/Users/kevintttccc/Library/Application Support/typora-user-images/image-20210708095519734.png)

## Kafka 2.8 变更

![image-20210708002724956](/Users/kevintttccc/Desktop/Technical Doc/Kafka/Kakfa-new.png)

### 架构变更

- 去掉 Zookeeper
- Quorum 控制器来选举 Active Controller
  -  使用 Raft 协议

- 元数据日志由 Active Controller 管理
  - 存放到  `metadata`  主题中
  - 备用节点主动同步最新数据

![image-20210708003459604](/Users/kevintttccc/Desktop/Technical Doc/Kafka/kafka-new-arch.png)

#### 新特性

- 元数据作为「事件日志」
- 元数据持久化到磁盘
  - 快速地启动新的 Broker（新节点只需要获取增量数据）
- Broker 和 Controller 的通信方式由 `Push` 改为 `Pull`

探讨一下为什么要去掉 Zookeeper？

- 降低维护成本
- 性能问题
- 避免 controller 状态和 zookeeper 状态不一致问题
  - 原来有什么问题？ 手动修改 zk 中状态，controller 不参与

