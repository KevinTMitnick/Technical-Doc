# 1. 为什么 Kafka 不使用内存进行数据存储？

​		由于 Kafka 是基于「Scala」和「Java」实现的，而 Scala 和 Java 均需要在 `JVM` 上运行，所以是基于内存的方式，即 「JVM 的堆」来进行数据存储则需要开辟很大的堆来支持数据读写，从而 `导致 GC频繁影响性能`。

​		考虑到这些因素，Kafka 是使用磁盘而不是 Kafka 服务器 「Broker 进程内存」来进行数据存储，并且基于：`磁盘顺序读写` 和 `mmap` 技术来实现高性能。

# 2. 存储结构

## 2.1 目录结构和文件结构

Kafka 是通过 `主题` 和 `分区` 来对消息进行分类的，所以存储结构也是基于分区来组织的，每个目录存放一个分区数据：

- 目录名：topic + partition

```pyth
案例：比如 Topic 名词是 mytopic，有两个分区，则对应的目录为：
		- mytopic-0
		- mytopic-1

查看 topic 详细信息：
# $KAFKA_HOME/bin/kafka-topics.sh --describe --topic mytopic --zookeeper localhost:2181
Topic:mytopic   PartitionCount:2    ReplicationFactor:2 Configs:
    Topic: mytopic  Partition: 0    Leader: 2   Replicas: 2,1   Isr: 2,1
    Topic: mytopic  Partition: 1    Leader: 0   Replicas: 0,2   Isr: 0,2
```

## 2.2 文件内容

### 2.2.1 数据文件和索引文件

​		Kafka 的文件主要有是两个（都是二进制文件）：

- 索引文件：*.index 结尾

  索引文件的内容是 `offset` 的「稀疏索引」，消费者消费时，Broker 根据消费着给的 offset 值，基于「二分查找」现在索引文件找到该 offset 对应的 `数据 segments 文件` 的位置，然后基于该位置（或往下）找到对应的数据。

- 数据文件：*.log 结尾

  整个分区的数据文件不是由一个文件存放的，而是有多个 `segments` 组成，即 `0000000.log` 文件就是其中的一个 segment 文件，命名方式：

  ```pyt
  文件名称 = 第一条数据在该分区的 offset 值
  ```

  一个 segment 文件大小是一定的，超过会创建新的文件，默认大小：1GB（可以在 server.properties 修改）。

  - 参数：`log.segment.bytes = 1073741824`

索引文件和 segment 的关系如下：

![](/Users/kevintttccc/Desktop/Technical Doc/Kafka/index+segment.webp)

### 2.2.2 为什么 Kafka 数据文件是二进制格式？

- 二进制的文件大小  <    文本文件更小；
- 可以减少数据传输、复制量
- 提高传输速率，节省网络带宽

### 2.2.3 索引文件的作用？

- 加快「数据文件」的检索速度

# 3. 消息写入

## 3.1 如何保证磁盘顺序读写？

- Producer 将消息发送到 Broker 时，根据消息的 Topic 和 Partition，将消息写入到该分区当前最后的 segment 文件，`文件的写入方式是追加写`。
- 由于是对 segment 文件追加写，故实现了对磁盘文件的顺序写，避免磁盘随机写时的磁盘寻道的开销，同时由于是追加写，故写入速度与磁盘文件大小无关。

## 3.2 页缓存 PageCache

- 虽然没有磁盘寻道的开销，但是「单条」消息都执行一次磁盘写入，会造成大量的磁盘 IO，影响性能；
- 所以在写入方面，Broker 基于 `mmap` 技术，即「内存映射文件」，将消息写入到页缓存中，由 「页缓存」直接映射到「磁盘文件」，不需要在 `用户空间 和 内核空间` 之间拷贝数据，所以可以认为消息传输时发送到内存中；
- 页缓存数据刷新同步 sync 到磁盘，是由操作系统来控制的，操作系统通过一个内核后台线程，每 5 秒检查一次是否需要将 页缓存 数据同步到磁盘文件，如果超过了 `指定时间` 或者 `指定大小` 则将数据同步到磁盘；

### 页缓存的优点？

- 如果重启 Kafka 服务（不是机器重启），页缓存中的数据还可以继续使用。

### 页缓存的缺点？

- 如果页缓存数据在没有刷新到磁盘文件之前，Broker 机器宕机了，则页缓存的数据也就丢失。

# 4. 消息读取

- Broker 接收到 Consumer 数据读取的请求之后，根据 Consumer 提供的：Topic、Partition、Partition offset 信息，然后 Broker 找到分区 `index` 和 `segment 文件`，通过「二分查找」定位给定的消息记录，最后通过「socket」传输给 Consumer。

## 4.1 零拷贝 zero-copy

参考：Kafka 之 zero-copy

- Broker 在从 segment 文件读取消息然后通过 socket 传输给消费者时，也是基于 `mmap` 技术实现了零拷贝读取

参考文档：https://juejin.cn/post/6844903495108132872

参考文档：http://ifeve.com/java-nio-scattergather/

#### 传统 I/O 与 Socket 交互



#### 使用 sendfile() 系统调用来支持 mmap 机制，实现零拷贝

具体过程如下：

- 应用指定需要传输的文件句柄和调用sendfile系统调用；
- 操作系统在内核读取磁盘文件拷贝到页缓存；
- 操作系统在内核将页缓存内容拷贝到网卡硬件缓存；

具体过程如图：

![](/Users/kevintttccc/Desktop/Technical Doc/Kafka/zero-copy.webp)

#### Java 的 sendfile 系统调用 API

- transferTo
- transferFrom

基于MMAP机制实现了磁盘文件内容的零拷贝传输。同时由于操作系统将磁盘文件内容加载到了内核页缓存，故消费者针对该磁盘文件的多次请求可以重复使用。